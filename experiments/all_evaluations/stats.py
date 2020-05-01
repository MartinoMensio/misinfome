import pandas as pd
import streamlit as st
import plotly.express as px
import datetime

from extract_articles_from_urls import get_url_domain

st.title('MisinfoMe URLs')
st.markdown('Run `python extract_articles_from_urls.py` to update the initial `joined_tables.tsv` table')

@st.cache(allow_output_mutation=True)
def load_table():
    #  with st.spinner('Loading table'):
    return pd.read_table('joined_tables.tsv', parse_dates=['publish_date', 'review_date'], date_parser=lambda col: pd.to_datetime(col, utc=True, errors = 'coerce'), dtype={'normalised_value': float})

df = load_table()
df['factchecker'] = df['review_url'].apply(get_url_domain)
df['ternary_label'] = df['normalised_score'].apply(lambda x: 'positive' if x > 0 else ('negative' if x < 0 else 'neutral'))
st.write(df.head())

st.text(f"Total table has {len(df)} rows, {len(df['url'].unique())} unique")
df_not_credible = df[df['normalised_score'] < 0]
st.text(f"Total table has {len(df_not_credible)} rows with non_credible, {len(df_not_credible['url'].unique())} unique")

# st.text(f'{len(df["in_covid_poynter"].unique())} unique in COVID-poynter')

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
    # from https://developer.twitter.com/en/docs/labs/covid19-stream/filtering-rules
    keywords_tw = ["#Coronavirusmexico", "#covid2019", "#coronavirususa", "#covid_19uk", "#covid-19uk", "#Briefing_COVID19", "#coronaapocolypse", "#coronavirusbrazil", "#marchapelocorona", "#coronavirusbrasil", "#coronaday", "#coronafest", "#coronavirusu", "#covid2019pt", "#COVID19PT", "#caronavirususa", "#covid19india", "#caronavirusindia", "#caronavirusoutbreak", "#caronavirus", "carona virus", "#2019nCoV", "2019nCoV", "#codvid_19", "#codvid19", "#conronaviruspandemic", "#corona", "corona", "corona vairus", "corona virus", "#coronadeutschland", "#Coronaferien", "#coronaflu", "#coronaoutbreak", "#coronapandemic", "#Coronapanik", "#coronapocalypse", "#CoronaSchlager", "#coronavid19", "#coronavid19", "#Coronavirus", "Coronavirus", "#coronavirusargentina", "#coronavirusbrasil", "#CoronaVirusCanada", "#coronaviruschile", "#coronaviruscolombia", "#CoronaVirusDE", "#coronavirusecuador", "#CoronavirusEnColombia", "#coronavirusespana", "CoronavirusFR", "#CoronavirusFR", "#coronavirusIndonesia", "#Coronavirusireland", "#CoronaVirusIreland", "#coronavirusmadrid", "#coronavirusmexico", "#coronavirusnobrasil", "#coronavirusnyc", "#coronavirusoutbreak", "#coronavirusoutbreak", "#coronaviruspandemic", "#coronavirusperu", "#coronaviruspuertorico", "#coronavirusrd", "#coronavirustruth", "#coronavirusuk", "coronavirusupdate", "#coronavirusupdates", "#coronavirusuruguay", "coronga virus", "corongavirus", "#Corvid19virus", "#covd19", "#covid", "covid", "#covid", "covid", "covid 19", "#covid_19", "#covid_19", "Covid_19", "#COVID_19uk", "#covid19", "Covid19", "Covid19_DE", "#covid19Canada", "Covid19DE", "Covid19Deutschland", "#covid19espana", "#covid19france", "#covid19Indonesia", "#covid19ireland", "#covid19uk", "#covid19usa", "#covid2019", "#ForcaCoronaVirus", "#infocoronavirus", "#kamitidaktakutviruscorona", "#nCoV", "nCoV", "#ncov2019", "nCoV2019", "NeuerCoronavirus", "#NeuerCoronavirus", "Nouveau coronavirus", "#NouveauCoronavirus", "novel coronavirus", "#NovelCorona", "novelcoronavirus", "#novelcoronavirus", "#NovelCoronavirus", "#NuovoCoronavirus", "#ohiocoronavirus", "#PánicoPorCoranovirus", "#SARSCoV2", "#SARSCoV2", "the coronas", "#thecoronas", "#trumpdemic", "Virus Corona", "#viruscorona", "فيروس كورونا", "#فيروس_كورونا", "#كورونا", "#كورونا_الجديد", "#कोरोना", "कोरोना", "कोरोना वायरस", "#कोरोना_वायरस", "코로나", "#코로나", "#코로나19", "코로나바이러스", "#코로나바이러스", "コロナ", "#コロナ", "#コロナウイルス", "加油武汉", "#加油武汉", "#新冠病毒", "新冠病毒", "#新冠肺炎", "新冠肺炎", "#新型コロナウイルス", "#新型冠状病毒", "新型冠状病毒", "武汉加油", "#武汉加油", "#武汉疫情", "#武汉肺炎", "武汉肺炎", "#武漢肺炎", "武漢肺炎", "疫情", "#疫情", "#CoronaAlert", "#coronavirusUP", "#coronavirustelangana", "#coronaviruskerala", "#coronavirusmumbai", "#coronavirusdelhi", "#coronavirusmaharashtra", "#coronavirusinindia", "वूहान", "#covid_19ind", "#covid19india", "coronavirus india", "#coronavirusindia", "#कोविड_19", "#कोविड-१९", "#कोरोनावायरस", "#bayarealockdown", "#stayathomechallenge", "#stayhomechallenge", "#quarantinelife", "#dontbeaspreader", "#stayhomechallenge", "#howtokeeppeoplehome", "#togetherathome", "alcool em gel", "alcool gel", "#alcoolemgel", "#alcoolgel", "#avoidcrowds", "bares cerrados", "bares fechados", "bars closed", "#canceleverything", "#CerradMadridYa", "clases anuladas", "#CLOSENYCPUBLICSCHOOLS", "#confinementtotal", "#CONVID19", "#CoronavirusESP", "cuarentena", "#cuarentena", "#CuarentenaCoronavirus", "#cuarentenaYA", "dont touch ur face", "dont touch your face", "#DontBeASpreader", "#donttouchyourface", "escolas fechadas", "escolas fechando", "escolas sem aula", "escolas sem aulas", "#euficoemcasa", "evitar el contagio", "#ficaemcasa", "flatten the curve", "flattening the curve", "#flatteningthecurve", "#flattenthecurve", "#FrenaLaCurva", "Hand sanitizer", "#Handsanitizer", "#HoldTheVirus", "lava tu manos", "#lavatumanos", "lave as maos", "#laveasmaos", "#lockdown", "lockdown", "#pandemic", "pandemic", "#panicbuying", "#panickbuing", "quarantaine", "#quarantine", "quarantine", "#QuarantineAndChill", "quarantined", "quarentena", "#quarentena", "#quarentine", "#quarentined", "quarentined", "#quarentinelife", "#quedateencasa", "#remotework", "#remoteworking", "restaurantes cerrados", "restaurantes fechados", "restaurants closed", "#selfisolating", "#SiMeContagioYo", "social distancing", "#socialdistance", "#socialdistancing", "#socialdistancingnow", "#socialdistnacing", "#stayathome", "#stayathome", "#stayhome", "#stayhome", "#stayhomechallenge", "#stayhomesavelives", "#StayTheFHome", "#StayTheFuckHome", "#suspendanlasclases", "teletrabajo", "#teletrabajo", "#ToiletPaperApocalypse", "#toiletpaperpanic", "trabajadores a la calle", "trabajar desde casa", "#trabajardesdecasa", "trabalhando de casa", "trabalhar de casa", "wash ur hands", "wash your hands", "#washurhands", "#washyourhands", "#WashYourHandsAgain", "#wfh", "work from home", "#workfromhome", "working from home", "#workingfromhome", "#yomequedoencasa"]
    keywords_tw = [k.replace('#', '') for k in keywords]
    keywords.extend(keywords_tw)
    r = any([k in str(txt).lower() for k in keywords])
    return r

year_2020_beginning = datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc)
df['corona'] = df.apply(lambda row: search_keywords(str(row['claim_reviewed']) + str(row['review_headline']) + str(row['review_body'])), axis=1)
covid_df = df[df['review_date'] > year_2020_beginning]
covid_df = covid_df[covid_df['corona']==True]
st.text(f'rows: {len(covid_df)}, unique urls: {len(covid_df["url"].unique())}, unique factchecking urls: {len(covid_df["review_url"].unique())}, negative urls: {len(covid_df[covid_df["ternary_label"] == "negative"]["url"].unique())}')
covid_df.to_csv('covid_table.tsv', sep='\t')
covid_df_without_body = covid_df.drop(columns=['body', 'review_body'])
covid_df_without_body['claim_reviewed'] = [str(el).replace('\n', ' ') for el in covid_df_without_body['claim_reviewed']]
covid_df_without_body.to_csv('covid_table_without_newlines.tsv', sep='\t')

fig = px.histogram(covid_df, x="review_date")
fig.update_layout(height=450)
st.plotly_chart(fig, use_container_width=True)

min_date = st.date_input('From date', datetime.date(2020, 1, 1))

min_datetime = datetime.datetime(min_date.year, min_date.month, min_date.day, tzinfo=datetime.timezone.utc)

# df['review_date'] = df['review_date'].dt.tz_localize('UTC', utc=True)
df_2020 = df[df['review_date'] > min_datetime]
st.text(f'rows: {len(df_2020)}, unique urls: {len(df_2020["url"].unique())}, unique factchecking urls: {len(df_2020["review_url"].unique())}, negative: {len(df_2020[df_2020["ternary_label"] == "negative"]["url"].unique())}')

df_2020.to_csv('table_2020.tsv', sep='\t')
df_2020_without_body = df_2020.drop(columns=['body', 'review_body'])
df_2020_without_body['claim_reviewed'] = [str(el).replace('\n', ' ') for el in df_2020_without_body['claim_reviewed']]
df_2020_without_body.to_csv('table_2020_without_newlines.tsv', sep='\t')

fig = px.histogram(df_2020, x="review_date")
fig.update_layout(height=450)
st.plotly_chart(fig, use_container_width=True)

