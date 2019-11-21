import requests
import os
import json
import dotenv
import plac
dotenv.load_dotenv()
BEARER_TOKEN = os.environ['BEARER_TOKEN']
misinfome_endpoint = 'https://misinfo.me/misinfo/api/credibility/users/'

def get_list_members(list_name, list_owner, update=False):
    # up to 5000 per single request
    if update:
        res = requests.get(f'https://api.twitter.com/1.1/lists/members.json?slug={list_name}&owner_screen_name={list_owner}&count=5000', headers={'Authorization': f'Bearer {BEARER_TOKEN}'})
        print(res.status_code)
        data = res.json()
        print(data)
        users = data['users']
        with open('data/users.json', 'w') as f:
            json.dump(users, f, indent=2)
    else:
        with open('data/users.json') as f:
            users = json.load(f)

    return users

def get_job_ids(users, update=False):
    if update:
        jobs_id = {}
        for u in users:
            res = requests.get(f'{misinfome_endpoint}?screen_name={u["screen_name"]}&wait=false')
            job_id = res.json()['job_id']
            jobs_id[u['screen_name']] = job_id
        with open('data/jobs_id.json', 'w') as f:
            json.dump(jobs_id, f, indent=2)
    else:
        with open('data/jobs_id.json') as f:
            jobs_id = json.load(f)
    return jobs_id

def get_statuses(jobs_id):
    results = {}
    for screen_name, jid in jobs_id.items():
        res = requests.get(f'https://misinfo.me/misinfo/api/jobs/status/{jid}')
        status = res.json()
        results[screen_name] = status
    with open('data/statuses.json', 'w') as f:
        json.dump(results, f, indent=2)
    return results

def analyse_results(results):
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
    with open('data/cred_dict.json', 'w') as f:
        json.dump(cred_dict, f, indent=2)
    return cred_dict
        

def do_things(list_name, list_owner):
    users = get_list_members(list_name, list_owner, update=True)
    jobs_id = get_job_ids(users, update=True)
    results = get_statuses(jobs_id)

    analyse_results(results)

if __name__ == "__main__":
    do_things('world-leaders', 'verified')
    