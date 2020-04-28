import pymongo
import csv
import json
import tldextract
import pandas as pd
from multiprocessing.pool import ThreadPool
from tqdm import tqdm
from goose3 import Goose
from langdetect import detect
from loguru import logger



# TODO all the unshortening
g = Goose()

mongo = pymongo.MongoClient()
documents_now_collection = mongo['articles_collection']['documents_now']
factchecking_collection = mongo['credibility']['factchecking_report']
claimreviews_collection = mongo['claimreview_scraper']['claim_reviews']

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

def retrieve_all(file_name):
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

def get_urls_table():
    ### retrieves the table urls (url, credibility_value, credibility_confidence, original_label, review_url)
    results = []
    url_level_assessments = factchecking_collection.find({'granularity': 'itemReviewed'})
    url_level_assessments = [el for el in url_level_assessments]
    print(len(url_level_assessments))
    for u in tqdm(url_level_assessments):
        url = u['itemReviewed']
        credibility_value = u['credibility']['value']
        credibility_confidence = u['credibility']['confidence']
        review_urls = u['original']['overall'].get('unknown', []) + u['original']['overall'].get('negative', []) + u['original']['overall'].get('positive', [])
        review_urls = list(set(review_urls))
        if len(review_urls) != 1:
            print('found', len(review_urls), 'for', url)
        matching_cr = claimreviews_collection.find({'url': {'$in': review_urls}})
        # TODO make them unique, for now they are multiple if the same claimReview is collected multiple times
        for cr in matching_cr:
            # TODO more details if alternateName not available
            rating = cr.get('reviewRating', {})
            original_label = rating.get('alternateName', f"{rating.get('ratingValue')} in [{rating.get('worstRating')}, {rating.get('bestRating')}]")
            r = {
                'url': url,
                'credibility_value': credibility_value,
                'credibility_confidence': credibility_confidence,
                'original_label': original_label,
                'review_url': cr['url'],
                'review_date': cr.get('datePublished'),
                'claim_reviewed': cr.get('claimReviewed')
            }
            found = False
            for c in results:
                unmatched_items = set(c.items()) ^ set(r.items())
                if not len(unmatched_items):
                    found= True
                    break
            if found:
                # print(c, r)
                # print('already there')
                # exit(1)
                pass
            else:
                results.append(r)

    with open('urls_labeled.json', 'w') as f:
        # writer = csv.DictWriter(f, fieldnames=r.keys(), delimiter='\t')
        # writer.writeheader()
        # writer.writerows(results)
        json.dump(results, f, indent=2)
    return results

def join_info(attach_poynter='/Users/mm35626/KMi/coinform/MisinfoMe/claimreview-scraper/poynter_covid.tsv'):
    with open('urls_labeled.json') as f:
        urls_labeled = json.load(f)
    
    if attach_poynter:
        # TODO pandas read, get unique fact-checking URLS
        df = pd.read_table(attach_poynter)
        poynter_fact_checking_urls = df['factchecker_url'].unique()
        print(len(poynter_fact_checking_urls))
    else:
        poynter_fact_checking_urls = False
    results = []
    for id, r in enumerate(tqdm(urls_labeled)):
        url = r['url']
        data = get_or_retrieve_url(url)
        if 'exception' in data:
            print('exception for', url)
            continue
        source = get_url_domain(url)
        # print(source)
        if source == 'twitter.com':
            # tweets data is in opengraph.description
            headline = data['opengraph'].get('title', '')
            body = data['opengraph'].get('description', '')
        elif source == 'facebook.com':
            headline = data['title']
            body = data['meta'].get('description', '')
            # print(headline, body)
            # raise ValueError(1)
        else:
            headline = data['title']
            body = data['cleaned_text']
        lang = detect_lang(body)
        publish_date = data['publish_date']
        factcheck_date = data['publish_date']
        if len(poynter_fact_checking_urls):
            covid_poynter = url in poynter_fact_checking_urls
        else:
            covid_poynter = False
        res = {
            'id': id,
            'url': url,
            'source': source,
            'headline': headline,
            'lang': lang,
            'body': body,
            'publish_date': publish_date,
            'factchecker_label': r['original_label'],
            'normalised_score': r['credibility_value'],
            'normalised_confidence': r['credibility_confidence'],
            'review_url': r['review_url'],
            'review_date': r['review_date'],
            'claim_reviewed': r['claim_reviewed'],
            'in_covid_poynter': covid_poynter
        }
        results.append(res)
    with open('joined_tables.tsv', 'w') as f:
        writer = csv.DictWriter(f, fieldnames=res.keys(), delimiter='\t')
        writer.writeheader()
        writer.writerows(results)

'''
A method returning the language of content. 
'''
def detect_lang(body):
    lang = 'lang_err'
    try:
        lang = detect(body)
    except Exception as e:
        logger.warning(e)
    finally:
        return lang

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

def main():
    # first get the table with the URLs
    get_urls_table()

    # then run the scraping of the destination pages (content and title using Goose)
    # retrieve_all('urls.tsv')

    # and finally join the initial table with the scraped content
    join_info()

if __name__ == "__main__":
    main()
