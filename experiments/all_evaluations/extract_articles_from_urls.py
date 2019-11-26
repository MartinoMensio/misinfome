import pymongo
import csv
from multiprocessing.pool import ThreadPool
from tqdm import tqdm
from goose3 import Goose

g = Goose()

mongo = pymongo.MongoClient()
documents_now_collection = mongo['articles_collection']['documents_now']

def get_url_cache(url):
    return documents_now_collection.find_one({'_id': url})

def save_url_cache(url_object):
    # add key
    url_object['_id'] = url_object['url']
    return documents_now_collection.insert_one(url_object)

def retrieve_url(url):
    try:
        article = g.extract(url=url)
        infos = article.infos
        infos['url'] = url
        return infos
    except Exception as e:
        return {
            'url': url,
            'exception': str(e)
        }

def get_or_retrieve_url(url):
    url_object = get_url_cache(url)
    if url_object:
        return url_object
    else:
        url_object = retrieve_url(url)
        save_url_cache(url_object)
        return url_object


def process_one(row):
    #print(r)
    url = row['key']
    url_object = get_or_retrieve_url(url)
    return url_object

def main(file_name):
    with open(file_name) as f:
        reader = csv.DictReader(f, delimiter='\t')
        rows = [r for r in reader]

    n_exceptions = 0
    with ThreadPool(32) as pool:
        for res in tqdm(pool.imap_unordered(process_one, rows), total=len(rows)):
            if 'exception' in res:
                print('exception', res['url'])
                n_exceptions += 1
    # TODO do something with the results
    print(n_exceptions)
    

if __name__ == "__main__":
    main('urls.tsv')