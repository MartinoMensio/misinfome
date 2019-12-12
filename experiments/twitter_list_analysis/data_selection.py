import datetime
import streamlit as st
import pandas as pd
from tqdm import tqdm
import requests
import matplotlib.pyplot as plt

import list_processing
import unshorten

st.title('Tweet selection')
st.markdown('Run `python mps_on_twitter.py` to update the initial `data/links_tweets.tsv` table')

@st.cache(allow_output_mutation=True)
def load_table():
    #  with st.spinner('Loading table'):
    return pd.read_table('data/links_tweets.tsv', parse_dates=['created_at'], dtype={'tweet_id': str, 'retweet': bool, 'retweet_source_tweet_id': str})

# @st.cache(persist=True)
# def unshorten_cached(url):
#     return unshorten.unshorten(url)

df = load_table()
# st.table(df.head())

all_links = df['link'].unique()
shared_links_unshort_map = unshorten.get_unshortened_tweets_urls(all_links)

fn = lambda val: shared_links_unshort_map[val]
df['link_unshortened'] = df['link'].apply(fn)


st.text(f"Loaded {len(df)} rows: \n"
    f"    {len(df['tweet_id'].unique())} distinct tweets from \n"
    f"    {len(df['screen_name'].unique())} profiles containing \n"
    f"    {len(df['link'].unique())} unique URLs")

choice = st.selectbox('How to select initial time', ['start', 'interval'])
if choice == 'start':
    start_date = st.date_input('Start date', datetime.date(2019, 11, 1))
else:
    days_ago = st.number_input('Days ago', 1, 60, 21, 1)
    start_date = st.date_input('Start date', datetime.date.today() - datetime.timedelta(days=days_ago))

# everything to datetime
start_datetime = pd.Timestamp(start_date)
st.text(f'Selected tweets from {start_datetime}')

df_time_filtered = df[df['created_at'] >= start_datetime]
st.text(f"Filtered {len(df_time_filtered)} rows: \n"
    f"    {len(df_time_filtered['tweet_id'].unique())} distinct tweets from \n"
    f"    {len(df_time_filtered['screen_name'].unique())} profiles containing \n"
    f"    {len(df_time_filtered['link'].unique())} unique URLs")

list_urls = unshorten.get_factchecked_urls()

st.text(f'Known URLs from fact-checkers: {len(list_urls)}')

st.text('Filtering with the known URLs')

retweeted = df_time_filtered[df_time_filtered['retweet'] == True]

st.text(f"Retweeted {len(retweeted['tweet_id'].unique())}")

# not unshortened
# df_link_filtered = df_time_filtered[df_time_filtered['link'].isin(list_urls)]

df_link_filtered = df_time_filtered[df_time_filtered['link_unshortened'].isin(list_urls)]
links_matching = df_link_filtered['link_unshortened'].unique()

@st.cache
def get_factcheck_for(url):
    """returns the factcheck {'url', 'value'} for the url reviewed"""
    res = requests.get('http://localhost:20300/urls/', params={'url': url})
    res.raise_for_status()
    report_match = next((el for el in res.json()['assessments'] if el['origin_id'] == 'factchecking_report'), None)
    if not report_match:
        print('not found for', url)
        url = None
        value = 0
    else:
        url = report_match['url']
        value = report_match['credibility']['value']
    return {'url': url, 'value': value}

st.text(f"Filtered {len(df_link_filtered)} rows: \n"
    f"    {len(df_link_filtered['tweet_id'].unique())} distinct tweets from \n"
    f"    {len(df_link_filtered['screen_name'].unique())} profiles containing \n"
    f"    {len(df_link_filtered['link_unshortened'].unique())} unique URLs")

# join with factcheck url and value
get_factcheck_url = lambda url: get_factcheck_for(url)['url']
get_factcheck_value = lambda url: get_factcheck_for(url)['value']
tqdm.pandas()
df_link_filtered['factcheck_url'] = df_link_filtered['link_unshortened'].progress_apply(get_factcheck_url)
df_link_filtered['factcheck_value'] = df_link_filtered['link_unshortened'].progress_apply(get_factcheck_value)
# join with party info
accounts_parties_dict = {el['screen_name']: el['party'] for el in list_processing.mps_on_twitter_get_list()}
print(accounts_parties_dict)
df_link_filtered['party'] = df_link_filtered['screen_name'].progress_apply(lambda el: accounts_parties_dict[el])
df_link_filtered['factchecker_domain'] = df_link_filtered['factcheck_url'].apply(lambda el: unshorten.get_url_domain(el))

only_ifcn = st.checkbox('Only IFCN fact-checks:', True)
if only_ifcn:
    ifcn_domains = unshorten.get_factchecker_domains()
    final_table = df_link_filtered[df_link_filtered['factchecker_domain'].isin(ifcn_domains)]
    st.text(f"IFCN filter selects {final_table.shape[0]} out of {df_link_filtered.shape[0]}")
    not_ifcn_domains = df_link_filtered[~df_link_filtered['factchecker_domain'].isin(ifcn_domains)]['factchecker_domain'].unique()
    st.text(f'cutting out {not_ifcn_domains}')
else:
    final_table = df_link_filtered

if st.checkbox('See table', False):
    st.table(final_table)

final_table.to_csv(f'data/mps_output_from_{start_date}_ifcn_{only_ifcn}.tsv', sep='\t')

def get_bucket(val):
    if val > 0:
        return 'true'
    elif val < 0:
        return 'false'
    else:
        return 'unknown'

final_table['easy_label'] = final_table['factcheck_value'].apply(get_bucket)
# by account and party
# index = pd.MultiIndex.from_frame(final_table)
# by_index = final_table.groupby()
grouped = final_table.groupby(['party', 'screen_name']).size()
# plt.hist(arr, bins=20)
plt.figure()
fig = grouped.unstack().plot(kind='bar', stacked=True, legend=False)
plt.tight_layout()
st.pyplot()

# plots
