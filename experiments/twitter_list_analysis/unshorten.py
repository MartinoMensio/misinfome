import requests
import tqdm
import os
import list_processing
import tldextract
import pymongo
from multiprocessing.pool import ThreadPool

mongo = pymongo.MongoClient()
ifcn_collection = mongo['credibility']['ifcn']

def unshorten(url):
    return _unshorten(url)['url_full']

def _unshorten(url):
    # endpoint = 'https://misinfo.me/misinfo/api/utils/unshorten'
    endpoint = 'http://localhost:5000/misinfo/api/utils/unshorten'
    try:
        response = requests.get(endpoint, params={'url': url})
        response.raise_for_status()
    except Exception as e:
        print(url, e)
        return None
    return response.json()


def unshorten_all(urls):
    with ThreadPool(16) as pool:
        res = {}
        for r in tqdm.tqdm(pool.imap_unordered(_unshorten, urls), total=len(urls), desc='Unshortening URLs'):
            if r:
                res[r['url']] = r['url_full']
        return res


def get_factchecked_urls():
    unshortened_urls_path = 'data/known_urls_unshortened.json'
    if os.path.exists(unshortened_urls_path):
        unshortened = list_processing.read_json(unshortened_urls_path)
    else:
        # list_1 = list_processing.read_json('data/known_urls_dataset_resources.json')
        list_urls = list_processing.read_json('data/known_urls_claimreview_scraper.json')
        # list_urls = list(set(list_1 + list_2))
        unshortened = unshorten_all(list_urls)
        list_processing.write_json(unshortened_urls_path, unshortened)
        
    return unshortened.values()

def get_unshortened_tweets_urls(urls):
    urls_unique = list(set(urls))
    unshortened_urls_path = 'data/mps_urls_unshortened.json'
    if os.path.exists(unshortened_urls_path):
        unshortened = list_processing.read_json(unshortened_urls_path)
    else:
        unshortened = {}
    to_unshorten = [el for el in urls_unique if el not in unshortened.keys()]
    print('urls', len(urls), 'urls_unique', len(urls_unique), 'to_unshorten', len(to_unshorten))
    
    for chunk in list_processing.split_in_chunks(to_unshorten, 10000):
        unshortened_new = unshorten_all(chunk)
        unshortened = {**unshortened, **unshortened_new}
        print('writing')
        list_processing.write_json(unshortened_urls_path, unshortened)
        print('written')

    result = {k: unshortened[k] for k in urls}
        
    return result

def get_url_domain(url, only_tld=True):
    """Returns the domain of the URL"""
    if not url:
        return ''
    ext = tldextract.extract(url)
    if not only_tld:
        result = '.'.join(part for part in ext if part)
    else:
        result = '.'.join([ext.domain, ext.suffix])
    if result.startswith('www.'):
            # sometimes the www is there, sometimes not
            result = result[4:]
    return result.lower()

def get_factchecker_domains():
    return ifcn_collection.distinct('itemReviewed')
