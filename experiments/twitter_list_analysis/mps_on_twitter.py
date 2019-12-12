import os
import requests
import tqdm
import csv
from multiprocessing.pool import ThreadPool
import dateparser


import list_processing

def get_tweets_from_screen_name(user):
    screen_name = user['screen_name']
    # on localhost because not public method on MisinfoMe
    try:
        response = requests.get(f'http://127.0.0.1:20200/search/tweets?screen_name={screen_name}')
        response.raise_for_status()
        tweets = response.json()
    except Exception as e:
        print(e)
        tweets = None
    return screen_name, tweets

def get_all_tweets(update_users=True, update_tweets=True, recollect_tweets=True):
    """
    - update_users: redownload user list
    - update_tweets: use API to get tweets or just use the local file
    - recollect_tweets: also for the profiles that we have already the tweets, rerun to collect the last tweets
    """
    original_list = list_processing.mps_on_twitter_get_list()
    if update_users:
        users = list_processing.lookup_users([el['screen_name'] for el in original_list], 'data/mps_on_twitter_users.json', force_update=update_users)
    else:
        # original_list = list_processing.read_json('data/mps_on_twitter_original_list.json')
        users = list_processing.read_json('data/mps_on_twitter_users.json')

    print('original list contains', len(original_list))
    print('twitter profiles retrieved through API', len(users))

    original_users_by_screen_name = { el['screen_name'].replace('@', ''): el for el in original_list }
    print('profiles not retrieved through API', set(original_users_by_screen_name.keys()) - set([el['screen_name'] for el in users]))

    tweets_by_screen_name_path = 'data/mps_tweets_by_screen_name.json'
    if update_tweets:
        tweets = {}
        if not recollect_tweets:
            if os.path.exists(tweets_by_screen_name_path):
                tweets = list_processing.read_json(tweets_by_screen_name_path)
        missing_tweet_collection = [u for u in original_list if u['screen_name'] not in tweets.keys()]
        updated = 0
        unsaved = False
        with ThreadPool(8) as pool:
            for screen_name, ts in tqdm.tqdm(pool.imap_unordered(get_tweets_from_screen_name, missing_tweet_collection), total=len(missing_tweet_collection), desc='Retrieving tweets'):
                # TODO if public user
                if ts:
                    tweets[screen_name] = ts
                    updated += 1
                    unsaved = True
                    if (updated % 100) == 99:
                        # save every 100 
                        list_processing.write_json(tweets_by_screen_name_path, tweets)
                        unsaved = False
        if unsaved:
            list_processing.write_json(tweets_by_screen_name_path, tweets)
    else:
        tweets = list_processing.read_json(tweets_by_screen_name_path)

    print('profiles with tweets', len(tweets.keys()))
    print('profiles without tweets', set([el['screen_name'] for el in users]) - set(tweets.keys()))
    return tweets

def create_tsv_plain_tweets_with_links(tweets_by_screen_name):
    result = []
    n_tweets = 0
    n_links = 0
    # tweets_by_screen_name = {k: v for i, (k,v) in enumerate(tweets_by_screen_name.items()) if i < 10}

    for screen_name, user_tweets in tqdm.tqdm(tweets_by_screen_name.items(), desc='Creating TSV of all the tweets with links'):
        for t in user_tweets:
            n_tweets += 1
            for l in t['links']:
                n_links += 1
                dt = dateparser.parse(t['created_at'].replace('+0000', ''))
                retweet_source = t.get('retweet_source_tweet')
                if not retweet_source:
                    retweet_source = {}
                result.append({
                    'screen_name': screen_name,
                    'tweet_id': t['id'],
                    'text': t['text'],
                    'retweet': t['retweet'],
                    'retweet_source_tweet_id': retweet_source.get('id'),
                    'retweet_source_tweet_text': retweet_source.get('text'),
                    'retweet_source_tweet_links': retweet_source.get('links'),
                    'link': l,
                    'created_at': dt.isoformat()
                })
    print('n_tweets', n_tweets)
    print('n_links', n_links)

    with open('data/links_tweets.tsv', 'w') as f:
        writer = csv.DictWriter(f, fieldnames=['screen_name', 'tweet_id', 'text', 'retweet', 'retweet_source_tweet_id', 'retweet_source_tweet_text', 'retweet_source_tweet_links', 'link', 'created_at'], delimiter='\t')
        writer.writeheader()
        writer.writerows(result)
    return result



def get_tweet_table():
    all_tweets = get_all_tweets(False, True, False)
    create_tsv_plain_tweets_with_links(all_tweets)


def main():
    get_tweet_table()
    
if __name__ == "__main__":
    main()
