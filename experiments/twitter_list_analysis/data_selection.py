import datetime
import streamlit as st
import pandas as pd
from tqdm import tqdm

import unshorten

st.title('Tweet selection')

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
    start_date = st.date_input('Start date', datetime.date.today() - datetime.timedelta(weeks=3))
else:
    days_ago = st.number_input('Days ago', 1, 60, 21, 1)
    start_date = st.date_input('Start date', datetime.date.today() - datetime.timedelta(days=days_ago))

st.text(f'Selected tweets from {start_date}')

df_time_filtered = df[df['created_at'] >= start_date]
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

df_link_filtered = df_time_filtered[df['link_unshortened'].isin(list_urls)]

st.text(f"Filtered {len(df_link_filtered)} rows: \n"
    f"    {len(df_link_filtered['tweet_id'].unique())} distinct tweets from \n"
    f"    {len(df_link_filtered['screen_name'].unique())} profiles containing \n"
    f"    {len(df_link_filtered['link_unshortened'].unique())} unique URLs")

st.table(df_link_filtered)