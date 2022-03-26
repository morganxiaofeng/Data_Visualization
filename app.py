import pandas as pd
from urllib.request import urlopen
import requests
import altair as alt
from vega_datasets import data
from altair import datum

url = "https://raw.githubusercontent.com/lukes/ISO-3166-Countries-with-Regional-Codes/master/all/all.json"
resp = requests.get(url)
country_info = resp.json()
country_info = pd.DataFrame(country_info)

stringency = pd.read_csv('https://raw.githubusercontent.com/morganxiaofeng/Data_Visualization/main/owid-covid-data_final.csv').loc[:,['iso_code','location','date','stringency_index']]

df = stringency[stringency['iso_code'].isin(country_info['alpha-3'])]
df = df.loc[df.date=='2021/12/31']


df['numericCode'] = df['iso_code'].replace(list(country_info['alpha-3']), list(country_info['country-code'])).astype(int)
df = df.dropna()


countries = alt.topo_feature(data.world_110m.url, 'countries')

background = alt.Chart(df).mark_geoshape()\
    .encode(color='stringency_index:Q')\
    .transform_lookup(
        lookup='numericCode',
        from_=alt.LookupData(countries, key='id',
                             fields=["type", "properties", "geometry"])
    )\
    .project('equirectangular')\
    .properties(
        width=500,
        height=400,
        title='Title'
    ).interactive()
