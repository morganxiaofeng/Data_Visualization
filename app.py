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
    sel_region,sel_index,sel_date,sel_vac = None, None, None, None

    st.sidebar.header('Choose options below')
    # 0) Need to reset data
    st.sidebar.markdown('Reset dataset?')
    if st.sidebar.button(label='Clear cache'):
        st.legacy_caching.clear_cache()
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
    if sel_date <= datetime.date(2021,12,31) and sel_date >= datetime.date(2021,1,1):
        st.success(f'Date: {sel_date}')
    else:
        st.error('Error: The date should be in Year 2021.')
    
    # 4) Compare with Political Index?
    if sel_index:
        st.sidebar.markdown('Draw a map to compare with the vaccination coverage (Booster Coverage, Fully-Vaccinated Coverage and Vaccinated-Once Coverage)?')
        check = st.sidebar.checkbox('Yes')
        if check:
            st.sidebar.markdown('Choose a stage of the vaccination (e.g., Booster Coverage)')
            sel_vac = st.sidebar.selectbox('Stage of Vaccination', ['Booster Coverage', 'Fully-Vaccinated Coverage', 'Vaccinated-Once Coverage'])
        else:
            sel_vac = None
     
    return sel_region, sel_index, sel_date, sel_vac



sel_region, sel_index, sel_date, sel_vac = display_sidebar(data)

###########################################################

coord_dict = {'World':[0,0], 'Africa':[8.7832,34.5085], 'Asia':[34.0479, 100.6197], 'Europe':[15.2551,54.5260], 
             'North America':[54.5260, -105.2551], 'Oceania':[-22.7359, 140.0188], 'South America':[-8.6048, -66.0625]}

# Set the viewport location
if sel_region == 'World':
    view_state = pdk.ViewState(latitude=coord_dict[sel_region][0], longitude=coord_dict[sel_region][1], zoom=0.5, bearing=0, pitch=0)
else:
    view_state = pdk.ViewState(latitude=coord_dict[sel_region][0], longitude=coord_dict[sel_region][1], zoom=1.5, bearing=0, pitch=0)

def color_scale(val):
    for i, b in enumerate(breaks):
        if val <= b:
            return color_range[i]
    return color_range[i]

def max_scale(val):
    return (val/val.max()).replace(np.nan,0).apply(color_scale)

src_geo = 'countries.json'
json_geo = pd.read_json(src_geo)
geo = pd.DataFrame()

# Parse the geometry out in Pandas
geo["coordinates"] = json_geo["features"].apply(lambda row: row["geometry"]["coordinates"])
geo["name"] = json_geo["features"].apply(lambda row: row["properties"]["name"])
geo["adm0_a3"] = json_geo["features"].apply(lambda row: row["properties"]["adm0_a3"])
geo["admin"] = json_geo["features"].apply(lambda row: row["properties"]["admin"])


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

###########################################################

index_dict = {'Stringency Index': 'stringency_index', 'GDP per Capita': 'gdp_per_capita', 'Human Development Index': 'human_development_index'}
variable = index_dict[sel_index]

index = pd.read_csv('owid-covid-data_final.csv').loc[:,['iso_code', 'date', 'stringency_index', 'gdp_per_capita', 'human_development_index']].rename(columns={'iso_code':'adm0_a3'})
df = pd.merge(index, geo, on='adm0_a3', how='left')
df['date'] = pd.to_datetime(df['date'])

df['fill_color'] = max_scale(df[variable])
df['variable'] = df[variable]
df['index'] = sel_index

df = df.loc[df.date == np.datetime64(sel_date)]
df = df.dropna(axis=0)
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
        

# Render
    
tooltip = {"html": "<b>Country/Region:</b> {admin} <br /><b>{index}:</b> {variable}"}

r = pdk.Deck(layers=[polygon_layer], initial_view_state=view_state, map_style='light', tooltip=tooltip)

st.pydeck_chart(r, use_container_width=True)




# Horizontal stacked bar chart

sel_vac = 'Booster Coverage'    
vac_dict = {'Booster Coverage': ['booster', 'booster_coverage'], 'Fully-Vaccinated Coverage': ['fully', 'fully_coverage'], 'Vaccinated-Once Coverage': ['once', 'once_coverage']}
variable_vac = vac_dict[sel_vac][0]

coverage = pd.read_csv('COVID_continent_income.csv').loc[:,['iso_code', 'location', 'date', 'people_vaccinated', 'people_fully_vaccinated', 'total_boosters', 'population']].rename(columns={'iso_code':'adm0_a3'})
df_vac = coverage.loc[coverage.location.isin(coord_dict.keys())]
df_vac['date'] = pd.to_datetime(df_vac['date'])
df_vac['coordinates'] = df_vac['location'].apply(lambda x: coord_dict[x])

df_vac['booster_coverage'] = (df_vac['total_boosters']/df_vac['people_vaccinated']).replace(np.nan,0)
df_vac['booster'] = max_scale(df_vac['booster_coverage'])
df_vac['fully_coverage'] = ((df_vac['people_fully_vaccinated']-df_vac['total_boosters'])/df_vac['people_vaccinated']).replace(np.nan,0)
df_vac['fully'] = max_scale(df_vac['fully_coverage'])
df_vac['once_coverage'] = ((df_vac['people_vaccinated']-df_vac['people_fully_vaccinated'])/df_vac['people_vaccinated']).replace(np.nan,0)
df_vac['once'] = max_scale(df_vac['once_coverage'])
df_vac['variable_vac'] = df_vac[vac_dict[sel_vac][1]]
df_vac['vac'] = sel_vac

df_vac = df_vac.loc[df_vac.date == np.datetime64(sel_date)]
df_vac = df_vac.dropna(axis=0)

df_vac_melt = pd.melt(df_vac.reset_index(), id_vars=['location'], value_vars=['booster_coverage','fully_coverage','once_coverage']).rename(columns={'variable': 'Stage of Vaccination', 'value': 'Coverage%', 'location': 'Continent'})
df_vac_melt['Coverage%'] = df_vac_melt['Coverage%'].apply(lambda x: round(x*100,2))

hover = alt.selection_single(fields=['Continent'], on='mouseover', nearest=True, init={'Continent': sel_region})

bars = alt.Chart(df_vac_melt).mark_bar().encode(
    x=alt.X('Coverage%', stack='zero', scale=alt.Scale(domain=(0, 100))),
    y=alt.Y('Continent'),
    color=alt.Color('Stage of Vaccination'),
    opacity=alt.condition(hover, alt.value(1.0), alt.value(0.3))
    ).add_selection(hover)


text = alt.Chart(df_vac_melt).mark_text(dx=-10, dy=3, color='white').encode(
    x=alt.X('Coverage%', stack='zero'),
    y=alt.Y('Continent'),
    detail='Stage of Vaccination:N',
    text=alt.Text('Coverage%', format='.1f'))

st.altair_chart(bars + text, use_container_width=True)







if sel_vac != None:
    
    # Define a layer to display on a map
    
    scatter_layer = pdk.Layer(
    "ScatterplotLayer",
    df_vac,
    pickable=True,
    opacity=0.8,
    stroked=True,
    filled=True,
    radius_scale=6,
    radius_min_pixels=1,
    radius_max_pixels=100,
    line_width_min_pixels=1,
    get_position="coordinates",
    get_radius=50000,
    get_fill_color=variable_vac,
    get_line_color=[0, 0, 0])

    # Render

    tooltipscatter = {"html": "<b>Continent:</b> {location} <br /><b>{vac}:</b> {variable_vac}%"}

    scatter = pdk.Deck(layers=[scatter_layer], initial_view_state=view_state, map_style='light', tooltip=tooltipscatter)

    st.pydeck_chart(scatter, use_container_width=True)
