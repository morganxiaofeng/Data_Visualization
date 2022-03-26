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

def color_scale(val):
    for i, b in enumerate(breaks):
        if val <= b:
            return color_range[i]
    return color_range[i]

stringency = pd.read_csv('owid-covid-data_final.csv').loc[:,['iso_code','location','date','stringency_index']].rename(columns={'iso_code':'adm0_a3'})

src_geo = 'countries.json'
json_geo = pd.read_json(src_geo)
df = pd.DataFrame()

# Parse the geometry out in Pandas
df["coordinates"] = json_geo["features"].apply(lambda row: row["geometry"]["coordinates"])
df["name"] = json_geo["features"].apply(lambda row: row["properties"]["name"])
df["adm0_a3"] = json_geo["features"].apply(lambda row: row["properties"]["adm0_a3"])
df["admin"] = json_geo["features"].apply(lambda row: row["properties"]["admin"])
df = pd.merge(stringency, df, on='adm0_a3', how='left')
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

df['fill_color'] = (df['stringency_index']/df['stringency_index'].max()).replace(np.nan,0).apply(color_scale)

# Choose a startdate to display
st.sidebar.header('Choose a startdate below')
st.sidebar.markdown('Choose a startdate (e.g., 2020-08-15)')
sel_date = st.sidebar.date_input('Date:', datetime.date(2021,12,31))
st.write(sel_date)

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
            pickable=True,
        )

# Set the viewport location
view_state = pdk.ViewState(latitude=0, longitude=0, zoom=1, bearing=0, pitch=0)

# Render
r = pdk.Deck(layers=[polygon_layer], initial_view_state=view_state)

st.pydeck_chart(r, use_container_width=True)
