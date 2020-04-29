import pandas as pd
import streamlit as st
import plotly.express as px

from extract_articles_from_urls import get_url_domain

st.title('MisinfoMe URLs')
st.markdown('Run `python extract_articles_from_urls.py` to update the initial `joined_tables.tsv` table')

@st.cache(allow_output_mutation=True)
def load_table():
    #  with st.spinner('Loading table'):
    return pd.read_table('joined_tables.tsv', parse_dates=['publish_date'], dtype={'normalised_value': float})

df = load_table()
df['factchecker'] = df['review_url'].apply(get_url_domain)
df['ternary_label'] = df['normalised_score'].apply(lambda x: 'positive' if x > 0 else ('negative' if x < 0 else 'neutral'))
st.write(df.head())

st.text(f"Total table has {len(df)} rows, {len(df['url'].unique())} unique")
df_not_credible = df[df['normalised_score'] < 0]
st.text(f"Total table has {len(df_not_credible)} rows with non_credible, {len(df_not_credible['url'].unique())} unique")

st.text(f'{len(df["in_covid_poynter"].unique())} unique in COVID-poynter')

fig = px.histogram(df, x="normalised_score")
fig.update_layout(height=450)
st.plotly_chart(fig, use_container_width=True)
fig = px.histogram(df, x="normalised_confidence")
fig.update_layout(height=450)
st.plotly_chart(fig, use_container_width=True)

fig = px.histogram(df, x="source")
fig.update_layout(height=450, yaxis_type="log")
st.plotly_chart(fig, use_container_width=True)

# see who factchecks the most
fig = px.histogram(df, x="factchecker", color="ternary_label")
fig.update_layout(height=450, yaxis_type="log")
st.plotly_chart(fig, use_container_width=True)

fig = px.histogram(df, x="lang")
fig.update_layout(height=450)
st.plotly_chart(fig, use_container_width=True)

fig = px.histogram(df, x="review_date")
fig.update_layout(height=450)
st.plotly_chart(fig, use_container_width=True)

fig = px.histogram(df, x="publish_date")
fig.update_layout(height=450)
st.plotly_chart(fig, use_container_width=True)

st.header('Covid')
# reviewed_claim
def search_keywords(txt):
    keywords = ['covid', 'coronavirus', 'corona virus']
    r = any([k in str(txt).lower() for k in keywords])
    return r

df['corona'] = df.apply(lambda row: search_keywords(row['claim_reviewed']), axis=1)
covid_df = df[df['corona']==True]
st.text(f'rows: {len(covid_df)}, unique: {len(covid_df["url"].unique())}, negative: {len(covid_df[covid_df["ternary_label"] == "negative"]["url"].unique())}')
covid_df.to_csv('covid_table.tsv', sep='\t')
covid_df_without_body = covid_df.drop(columns=['body'])
covid_df_without_body['claim_reviewed'] = [str(el).replace('\n', ' ') for el in covid_df_without_body['claim_reviewed']]
covid_df_without_body.to_csv('covid_table_without_newlines.tsv', sep='\t')
