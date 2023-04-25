import pymongo
import csv
import json
import tldextract
import pandas as pd
from collections import defaultdict
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
claimreviews_collection = mongo['claimreview_collector']['claim_reviews']


def get_url_cache(url):
    return documents_now_collection.find_one({'_id': url})

def save_url_cache(url_object):
    # add key
    url_object['_id'] = url_object['url']
    return documents_now_collection.replace_one({'_id': url_object['_id']}, url_object, upsert=True)

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

    # group the claimReviews by url
    all_cr_by_url = defaultdict(list)
    for cr in claimreviews_collection.find():
        # print(cr['url'])
        all_cr_by_url[cr['url']].append(cr)

    # TODO need the function to get the claim appearances (import credibility or copy function)
    # TODO create dict {appearance_url: list(claimreview_url)}

    for u in tqdm(url_level_assessments):
        url = u['itemReviewed']
        credibility_value = u['credibility']['value']
        credibility_confidence = u['credibility']['confidence']
        review_urls = u['original']['overall'].get('unknown', []) + u['original']['overall'].get('negative', []) + u['original']['overall'].get('positive', [])
        review_urls = list(set(review_urls))
        if len(review_urls) != 1:
            print('found', len(review_urls), 'for', url)
        matching_cr = [cr for cr_url in review_urls for cr in all_cr_by_url[cr_url]]
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

def join_info(attach_poynter='/Users/mm35626/KMi/coinform/MisinfoMe/claimreview-collector/poynter_covid.tsv'):
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

    with ThreadPool(32) as pool:
        for row in tqdm(pool.imap(join_one_row, enumerate(urls_labeled)), total=len(urls_labeled)):
            if row:
                results.append(row)

    with open('joined_tables.tsv', 'w') as f:
        writer = csv.DictWriter(f, fieldnames=row.keys(), delimiter='\t')
        writer.writeheader()
        writer.writerows(results)


def join_one_row(args):
    id, r = args
    url = r['url']
    if not url.startswith('http'):
        # not a URL
        return None
    data = get_or_retrieve_url(url)
    source = get_url_domain(url)
    if 'exception' in data:
        print('exception for', url)
        headline = ''
        body = ''
        lang = 'lang_error'
        publish_date = ''
        # return None
    else:
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

    data_review = get_or_retrieve_url(r['review_url'])
    if 'exception' in data_review:
        print('exception for', r['review_url'])
        headline_review = ''
        body_review = ''
        # return None
    else:
        headline_review = data_review['title']
        body_review = data_review['cleaned_text']

    # if len(poynter_fact_checking_urls):
    #     covid_poynter = url in poynter_fact_checking_urls
    # else:
    #     covid_poynter = False
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
        'review_headline': headline_review,
        'review_body': body_review,
        'claim_reviewed': r['claim_reviewed'],
        # 'in_covid_poynter': covid_poynter
    }
    return res

'''
A method returning the language of content. 
'''
def detect_lang(body):
    lang = 'lang_err'
    try:
        lang = detect(body)
    except Exception as e:
        # logger.warning(e)
        pass
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
