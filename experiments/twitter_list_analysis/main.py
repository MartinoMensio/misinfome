import requests
import os
import json
import dotenv
import plac
import csv

dotenv.load_dotenv()
BEARER_TOKEN = os.environ['BEARER_TOKEN']
misinfome_endpoint = 'https://misinfo.me/misinfo/api/credibility/users/'

def get_list_members(list_name, list_owner):
    # up to 5000 per single request
    file_path = f'data/{list_name}_{list_owner}_users.json'
    # the call is done again if the file does not exist
    update = not os.path.exists(file_path)
    print('getting list members', update)
    if update:
        res = requests.get(f'https://api.twitter.com/1.1/lists/members.json?slug={list_name}&owner_screen_name={list_owner}&count=5000', headers={'Authorization': f'Bearer {BEARER_TOKEN}'})
        print(res.status_code)
        data = res.json()
        #print(data)
        users = data['users']
        with open(file_path, 'w') as f:
            json.dump(users, f, indent=2)
    else:
        with open(file_path) as f:
            users = json.load(f)

    return users

def get_job_ids(users, name_prefix):
    file_path = f'data/{name_prefix}_jobs_id.json'
    # the call is done again if the file does not exist
    update = not os.path.exists(file_path)
    print('getting job ids', update)
    if update:
        jobs_id = {}
        for u in users:
            res = requests.get(f'{misinfome_endpoint}?screen_name={u["screen_name"]}&wait=false')
            job_id = res.json()['job_id']
            jobs_id[u['screen_name']] = job_id
        with open(file_path, 'w') as f:
            json.dump(jobs_id, f, indent=2)
    else:
        with open(file_path) as f:
            jobs_id = json.load(f)
    return jobs_id

def get_jobs_status(jobs_id, name_prefix):
    file_path = f'data/{name_prefix}_jobs_status.json'
    # the call is done again if the file does not exist
    if os.path.exists(file_path):
        with open(file_path) as f:
            results = json.load(f)
    else:
        results = {}
    jobs_ids_not_done = {k: v for k,v in jobs_id.items() if results.get(k, {}).get('state') != 'SUCCESS'}
    print(f'getting the status of {len(jobs_ids_not_done)}/{len(jobs_id)} of the uncompleted jobs')
    for screen_name, jid in jobs_ids_not_done.items():
        res = requests.get(f'https://misinfo.me/misinfo/api/jobs/status/{jid}')
        status = res.json()
        results[screen_name] = status
    with open(file_path, 'w') as f:
        json.dump(results, f, indent=2)
    return results

def analyse_results(results, name_prefix):
    print('analysing the results')
    n_done = 0
    n_failures = 0
    n_pending = 0
    n_positive = 0
    n_negative = 0
    n_neutral = 0
    cred_dict = {}
    for screen_name, result in results.items():
        if result['state'] == 'SUCCESS':
            n_done += 1
            if result['result']['credibility']['value'] > 0.2:
                n_positive += 1
            elif result['result']['credibility']['value'] < -0.2:
                n_negative += 1
            else:
                n_neutral += 1
            cred_dict[screen_name] = result['result']['credibility']
        elif result['state'] == 'FAILURE':
            n_failures += 1
        else:
            n_pending += 1
    
    print('n_done', n_done, 'n_failures', n_failures, 'n_pending', n_pending, 'n_positive', n_positive, 'n_negative', n_negative, 'n_neutral', n_neutral)
    with open(f'data/{name_prefix}_cred_dict.json', 'w') as f:
        json.dump(cred_dict, f, indent=2)
    return cred_dict
        

def process_list(list_name, list_owner, update=True):
    # from a list URL https://twitter.com/${LIST_OWNER}/lists/{LIST_NAME}/members get the LIST_NAME and LIST_OWNER params
    users = get_list_members(list_name, list_owner)

    process_twitter_users(users, f'{list_name}_{list_owner}')

def process_twitter_users(users, name_prefix):
    # users is an array of user objects from Twitter API
    jobs_id = get_job_ids(users, name_prefix)
    results = get_jobs_status(jobs_id, name_prefix)

    to_tsv(results, name_prefix)
    analyse_results(results, name_prefix)

def msp_on_twitter_get_list():
    list_endpoint = 'https://www.mpsontwitter.co.uk/api/list/name?order=ASC'
    res = requests.get(list_endpoint)
    print(res.status_code)
    data = res.json()
    with open('data/mps_on_twitter_original_list.json', 'w') as f:
        json.dump(data, f, indent=2)
    return data

def split_in_chunks(iterable, chunk_size):
    for i in range(0, len(iterable), chunk_size):
        yield iterable[i:i+chunk_size]

def lookup_users(users_screen_names, file_path=None):
    if file_path:
        update = not os.path.exists(file_path)
    else:
        update = True
    if update:
        users = []
        # users lookup has limit 100 by request
        for chunk in split_in_chunks(users_screen_names, 100):
            params = {
                'screen_name': ','.join([str(el) for el in chunk])
            }
            # print(params)
            res = requests.post('https://api.twitter.com/1.1/users/lookup.json', params=params, headers={'Authorization': f'Bearer {BEARER_TOKEN}'})
            print(res.status_code)
            new_users = res.json()
            users.extend(new_users)
        with open(file_path, 'w') as f:
            json.dump(users, f, indent=2)
    else:
        with open(file_path) as f:
            users = json.load(f)
    return users


def msp_on_twitter_process():
    # Prospective Parliamentary Candidates from https://www.mpsontwitter.co.uk/list
    original_list = msp_on_twitter_get_list()
    users = lookup_users([el['screen_name'].replace('@', '') for el in original_list], 'data/mps_on_twitter_users.json')

    process_twitter_users(users, 'mps_on_twitter')


def to_tsv(results, name_prefix):
    n_max_bad_sources = 0
    n_max_bad_urls = 0
    n_max_bad_tweets = 0 # from credibility_as_source
    selections = []
    for k, r in results.items():
        selection = {}
        # print(selection['screen_name'])
        if r['state'] != 'SUCCESS':
            selection['screen_name'] = k
        else:
            selection['screen_name'] = r['result']['itemReviewed']['screen_name']
            selection['tweets_cnt'] = r['result']['itemReviewed']['tweets_cnt']
            selection['shared_urls_cnt'] = r['result']['itemReviewed']['shared_urls_cnt']
            selection['credibility.value'] = r['result']['credibility']['value']
            selection['credibility.confidence'] = r['result']['credibility']['confidence']
            bad_sources = [el['itemReviewed'] for el in r['result']['sources_credibility']['assessments'] if el['credibility']['value'] < 0.]
            if len(bad_sources) > n_max_bad_sources:
                n_max_bad_sources = len(bad_sources)
            bad_urls = [el['itemReviewed'] for el in r['result']['urls_credibility']['assessments'] if el['credibility']['value'] < 0.]
            if len(bad_urls) > n_max_bad_urls:
                n_max_bad_urls = len(bad_urls)
            # selection['checked_as_source'] = True if r['result']['profile_as_source_credibility'].get('assessments') else False
            selection['bad_sources'] = bad_sources
            selection['bad_urls'] = bad_urls

        selections.append(selection)
    
    def replace_to_array(dictionary, key):
        if key in dictionary:
            val = dictionary[key]
            del dictionary[key]
            for i, el in enumerate(val):
                dictionary[f'{key}_{i+1}'] = el

    print('n_max_bad_sources', n_max_bad_sources)
    print('n_max_bad_urls', n_max_bad_urls)
    selections_keys = {k: 'foo' for k in selections[0].keys()}
    selections_keys['bad_sources'] = ['foo' for i in range(n_max_bad_sources)]
    selections_keys['bad_urls'] = ['foo' for i in range(n_max_bad_urls)]
    replace_to_array(selections_keys, 'bad_sources')
    replace_to_array(selections_keys, 'bad_urls')
    print(selections_keys)

    for r in selections:
        replace_to_array(r, 'bad_sources')
        replace_to_array(r, 'bad_urls')



    with open(f'data/{name_prefix}_table.tsv', 'w') as f:
        writer = csv.DictWriter(f, fieldnames=selections_keys.keys(), delimiter='\t')
        writer.writeheader()
        writer.writerows(selections)

if __name__ == "__main__":
    process_list('world-leaders', 'verified')
    process_list('uk-mps', 'twittergov')
    msp_on_twitter_process()
    