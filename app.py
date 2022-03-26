import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import math
from urllib.request import urlopen
import requests
import altair as alt
# from vega_datasets import data
# from altair import datum
import datetime

data = pd.read_csv('owid-covid-data_final.csv')

def display_sidebar(data):
    sel_region,sel_index = None, None

    st.sidebar.header('Choose options below')
    # 0) Need to reset data
    st.sidebar.markdown('Reset dataset?')
    if st.sidebar.button(label='Clear cache'):
        st.caching.clear_cache()
        st.experimental_rerun()

    # 1) Choose a Region/Country to display
    st.sidebar.markdown('Choose a Continent (e.g., Europe)')
    
    sel_region = st.sidebar.selectbox('Continent',['World', 'Africa', 'Asia', 'Europe', 'North America', 'Oceania', 'South America'])

    # 2) Choose a Political Index
    st.sidebar.markdown('Choose a Political Index (e.g., Stringency Index)')
    
    sel_index = st.sidebar.selectbox('Political Index', ['Stringency Index', 'GDP per Capita', 'Human Development Index'])
        
    # 3) Choose a date to display
    st.sidebar.header('Choose a date below')
    st.sidebar.markdown('Choose a date (e.g., 2020-08-15)')
    sel_date = st.sidebar.date_input('Date:', datetime.date(2021,12,31))
    st.write(sel_date)
     
    return sel_region, sel_index, sel_date



sel_region, sel_index, sel_date = display_sidebar(data)
cord_dict = {'World':[0,0], 'Africa':[8.7832,34.5085], 'Asia':[100.6197,34.0479], 'Europe':[15.2551,54.5260], 
             'North America':[105.2551,54.5260], 'Oceania':[140.0188, 22.7359], 'South America':[55.4915, 8.7832]}
index_dict = {'Stringency Index': 'stringency_index', 'GDP per Capita': 'gdp_per_capita', 'Human Development Index': 'human_development_index'}
variable = index_dict[sel_index]
def color_scale(val):
    for i, b in enumerate(breaks):
        if val <= b:
            return color_range[i]
    return color_range[i]

index = pd.read_csv('owid-covid-data_final.csv').loc[:,['iso_code', 'date', 'stringency_index', 'gdp_per_capita', 'human_development_index']].rename(columns={'iso_code':'adm0_a3'})

src_geo = 'countries.json'
json_geo = pd.read_json(src_geo)
df = pd.DataFrame()

# Parse the geometry out in Pandas
df["coordinates"] = json_geo["features"].apply(lambda row: row["geometry"]["coordinates"])
df["name"] = json_geo["features"].apply(lambda row: row["properties"]["name"])
df["adm0_a3"] = json_geo["features"].apply(lambda row: row["properties"]["adm0_a3"])
df["admin"] = json_geo["features"].apply(lambda row: row["properties"]["admin"])
df = pd.merge(index, df, on='adm0_a3', how='left')
df['date'] = pd.to_datetime(df['date'])

breaks = [.0, .2, .4, .6, .8, 1]
color_range = [
    # 6-class Blues
    [255,255,255],
    [198,219,239],
    [158,202,225],
    [107,174,214],
    [49,130,189],
    [8,81,156],

    # # 6-class Purples (For reference)
    # [242,240,247],
    # [218,218,235],
    # [188,189,220],
    # [158,154,200],
    # [117,107,177],
    # [84,39,143],
    ]

df['fill_color'] = (df[variable]/df[variable].max()).replace(np.nan,0).apply(color_scale)
df['variable'] = df[variable]
df['index'] = sel_index

if sel_date <= datetime.date(2021,12,31) and sel_date >= datetime.date(2021,1,1):
    st.success(f'Date: {sel_date}')
else:
    st.error('Error: The date should be in Year 2021.')
df = df.loc[df.date == np.datetime64(sel_date)]
df = df.dropna()

# Define a layer to display on a map
polygon_layer = pdk.Layer(
            "PolygonLayer",
            df,
            id="geojson",
            opacity=0.2,
            stroked=False,
            get_polygon="coordinates",
            filled=True,
            # get_elevation='elevation',
            # elevation_scale=1e5,
            # elevation_range=[0,100],
            extruded=True,
            # wireframe=True,
            get_fill_color= 'fill_color',
            get_line_color=[255, 255, 255],
            auto_highlight=True,
            pickable=True)
        

# Set the viewport location
view_state = pdk.ViewState(latitude=cord_dict[sel_region][0], longitude=cord_dict[sel_region][1], zoom=1, bearing=0, pitch=0)

# Render
    
tooltip = {"html": "<b>Country/Region:</b> {admin} <br /><b>{index}:</b> {variable}"}

r = pdk.Deck(layers=[polygon_layer], initial_view_state=view_state, map_style='light', tooltip=tooltip)

st.pydeck_chart(r, use_container_width=True)
