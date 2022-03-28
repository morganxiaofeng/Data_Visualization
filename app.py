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

st.header('COVID-19 Progress: Evolution of Emerging Cases & Vaccination in 2021')

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
    
    sel_region = st.sidebar.selectbox('Continent:',['World', 'Africa', 'Asia', 'Europe', 'North America', 'Oceania', 'South America'])

    # 2) Choose a Macroenvironmental Index
    st.sidebar.header('Regional Analysis)
    st.sidebar.markdown('Choose a Macroenvironmental Index (e.g., Stringency Index)')
    
    sel_index = st.sidebar.selectbox('Macroenvironmental Index:', ['Stringency Index', 'GDP per Capita', 'Human Development Index'])
        
    # 3) Choose a date to display
    
    st.sidebar.markdown('Choose a date in 2021 (e.g., 2020-08-15)')
    sel_date = st.sidebar.date_input('Date:', datetime.date(2021,12,31))
    if sel_date > datetime.date(2021,12,31) and sel_date < datetime.date(2021,1,1):
        st.error('Error: The date should be in Year 2021.')
    
    # 4) Compare with Macroenvironmental Index?
    if sel_index:
        st.sidebar.markdown('Draw a map to compare with the vaccination coverage (Booster Coverage, Vaccinated Fully Coverage and Vaccinated Once Coverage)?')
        check = st.sidebar.checkbox('Yes')
        if check:
            st.sidebar.markdown('Choose a stage of the vaccination (e.g., Booster Coverage)')
            sel_vac = st.sidebar.selectbox('Stage of Vaccination', ['Booster Coverage', 'Vaccinated Fully Coverage', 'Vaccinated Once Coverage'])
        else:
            sel_vac = None
     
    return sel_region, sel_index, sel_date, sel_vac


sel_region, sel_index, sel_date, sel_vac = display_sidebar(data)

###########################################################

coord_dict = {'World':[0,0], 'Africa':[8.7832,34.5085], 'Asia':[34.0479, 100.6197], 'Europe':[54.5260, 15.2551], 
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

# Hover setting
hover = alt.selection_single(fields=['Continent'], on='mouseover', nearest=True, init={'Continent': sel_region})
if sel_region == 'World':
    colorvac = alt.Color('mean(New Vaccinations Smoothed):Q',scale=alt.Scale(scheme='blues'), title='New Vaccinations (AVG)')
    colorcas = alt.Color('mean(New Cases Smoothed):Q',scale=alt.Scale(scheme='blues'), title='New Cases (AVG)')
    opacity = alt.value(1)
else:
    colorvac = alt.condition(hover, alt.Color('mean(New Vaccinations Smoothed):Q',scale=alt.Scale(scheme='blues')), alt.value('lightgray'), title='New Vaccinations (AVG)')
    colorcas = alt.condition(hover, alt.Color('mean(New Cases Smoothed):Q',scale=alt.Scale(scheme='blues')), alt.value('lightgray'), title='New Cases (AVG)')
    opacity = alt.condition(hover, alt.value(1.0), alt.value(0.05))
###########################################################


vac_case = pd.read_csv('COVID_continent_income.csv').loc[:,['location', 'date', 'new_vaccinations_smoothed', 'new_cases_smoothed', 'total_vaccinations', 'total_cases']].rename(columns={'iso_code':'adm0_a3'})
df_vac_case = vac_case.loc[vac_case.location.isin(list(coord_dict.keys())[1:])].rename(columns={'location': 'Continent', 'date': 'Date', 'new_vaccinations_smoothed': 'New Vaccinations Smoothed', 'new_cases_smoothed': 'New Cases Smoothed'})
df_vac_case['Date'] = pd.to_datetime(df_vac_case['Date'])
df_vac_case = df_vac_case.fillna(0)
dates = df_vac_case['Date'].map(lambda x:x.strftime('%m/%d/%y')).unique().tolist()


# Stacked Area Chart
st.header('Global View of Cases & Vaccinations')
st.subheader('Evolution of New Confirmed Cases in 2021 per Continent')

area = alt.Chart(df_vac_case).mark_area().encode(
    x=alt.X('Date', sort=dates),
    y=alt.Y("New Cases Smoothed", title='New Confirmed Cases'),
    color="Continent:N",
    opacity=opacity,
    tooltip=['Continent','Date', alt.Tooltip('New Cases Smoothed',title='New Confirmed Cases')]
).configure_scale(bandPaddingInner=.1).add_selection(hover)

st.altair_chart(area, use_container_width=True)

# Line Chart

st.subheader('Evolution of Total Vaccinations and Total Cases in 2021 per Continent')

line_vac = alt.Chart(df_vac_case).mark_line().encode(
    x="Date:T",
    y=alt.Y("total_vaccinations", title='Total Vaccinations'),
    color="Continent:N",
    opacity=opacity,
    tooltip=['Continent','Date', alt.Tooltip("total_vaccinations", title='Total Vaccinations')]
    ).add_selection(hover)

line_cas = alt.Chart(df_vac_case).mark_line().encode(
    x="Date:T",
    y=alt.Y("total_cases", title='Total Cases'),
    color="Continent:N",
    opacity=opacity,
    tooltip=['Continent','Date', alt.Tooltip("total_cases", title='Total Cases')]
    ).add_selection(hover)

st.altair_chart(alt.vconcat(line_vac,line_cas).configure_scale(bandPaddingInner=.1), use_container_width=True)

# Heatmap
st.header('Regional Analysis')
st.subheader('Monthly Evolution of New Vaccinations Smoothed in 2021')

vac_heatmap = alt.Chart(df_vac_case).mark_rect().encode(
                                x=alt.X('month(Date):O', sort=dates),
                                y=alt.Y('Continent'),
                                color=colorvac,
                                opacity=opacity,
                                tooltip=['Continent', 'Date', 'New Vaccinations Smoothed', 'New Cases Smoothed']
                                ).add_selection(hover).interactive().configure_scale(bandPaddingInner=.1)

st.altair_chart(vac_heatmap, use_container_width=True)

st.subheader('Monthly Evolution of New Cases Smoothed in 2021')
case_heatmap = alt.Chart(df_vac_case).mark_rect().encode(
                                x=alt.X('month(Date):O', sort=dates),
                                y=alt.Y('Continent'),
                                color=colorcas,
                                opacity=opacity,
                                tooltip=['Continent', 'Date', 'New Vaccinations Smoothed', 'New Cases Smoothed']
                                ).add_selection(hover).interactive().configure_scale(bandPaddingInner=.1)

st.altair_chart(case_heatmap, use_container_width=True)


# Macroenvironmental geo map
index_dict = {'Stringency Index': 'stringency_index', 'GDP per Capita': 'gdp_per_capita', 'Human Development Index': 'human_development_index'}
variable = index_dict[sel_index]

index = pd.read_csv('owid-covid-data_final.csv').loc[:,['iso_code', 'date', 'location', 'continent', 'stringency_index', 'gdp_per_capita', 'human_development_index', 'total_vaccinations', 'population']].rename(columns={'iso_code':'adm0_a3', 'continent': 'Continent'})
df = pd.merge(index, geo, on='adm0_a3', how='left')
df['date'] = pd.to_datetime(df['date'])

df['fill_color'] = max_scale(df[variable])
df['variable'] = df[variable]
df['index'] = sel_index

df = df.loc[df.date == np.datetime64(sel_date)]
df = df.dropna(axis=0)
# Define a layer to display on a map

st.header('How is the situation of macroenvironmental indexes and how is related to vaccinations?')

st.success(f'Date: {sel_date}')

st.subheader(f'Macroenvironmental Index Heatmap on {sel_date}')

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
 

coverage = pd.read_csv('COVID_continent_income.csv').loc[:,['iso_code', 'location', 'date', 'people_vaccinated', 'people_fully_vaccinated', 'total_boosters', 'population']].rename(columns={'iso_code':'adm0_a3'})
df_vac = coverage.loc[coverage.location.isin(coord_dict.keys())]
df_vac['date'] = pd.to_datetime(df_vac['date'])
df_vac['coordinates'] = df_vac['location'].apply(lambda x: [coord_dict[x][1],coord_dict[x][0]])

df_vac['Booster Coverage'] = (df_vac['total_boosters']/df_vac['people_vaccinated']).replace(np.nan,0)
df_vac['booster'] = max_scale(df_vac['Booster Coverage'])
df_vac['Vaccinated Fully Coverage'] = ((df_vac['people_fully_vaccinated']-df_vac['total_boosters'])/df_vac['people_vaccinated']).replace(np.nan,0)
df_vac['fully'] = max_scale(df_vac['Vaccinated Fully Coverage'])
df_vac['Vaccinated Once Coverage'] = ((df_vac['people_vaccinated']-df_vac['people_fully_vaccinated'])/df_vac['people_vaccinated']).replace(np.nan,0)
df_vac['once'] = max_scale(df_vac['Vaccinated Once Coverage'])


df_vac = df_vac.loc[df_vac.date == np.datetime64(sel_date)]
df_vac = df_vac.dropna(axis=0)

df_vac_melt = pd.melt(df_vac.reset_index(), id_vars=['location'], value_vars=['Booster Coverage','Vaccinated Fully Coverage','Vaccinated Once Coverage']).rename(columns={'variable': 'Stage of Vaccination', 'value': 'Coverage%', 'location': 'Continent'})
df_vac_melt['Coverage%'] = df_vac_melt['Coverage%'].apply(lambda x: round(x*100,2))

st.subheader(f'Vaccination Coverage Pertancages per Dose on {sel_date} in Different Continents')

bars = alt.Chart(df_vac_melt).mark_bar().encode(
    x=alt.X('Coverage%', stack='zero', scale=alt.Scale(domain=(0, 100))),
    y=alt.Y('Continent'),
    color=alt.Color('Stage of Vaccination'),
    opacity=opacity,
    tooltip=['Stage of Vaccination','Continent','Coverage%']
    ).add_selection(hover)


st.altair_chart(bars.configure_scale(bandPaddingInner=.1).interactive(), use_container_width=True)


if sel_vac != None:
    vac_dict = {'Booster Coverage': ['booster', 'Booster Coverage'], 'Vaccinated Fully Coverage': ['fully', 'Vaccinated Fully Coverage'], 'Vaccinated Once Coverage': ['once', 'Vaccinated Once Coverage']}
    variable_vac = vac_dict[sel_vac][0]
    df_vac['variable_vac'] = round(df_vac[vac_dict[sel_vac][1]]*100, 2)
    df_vac['vac'] = sel_vac
    
    # Define a layer to display on a map
    
    scatter_layer = pdk.Layer(
    "ScatterplotLayer",
    df_vac.loc[df_vac.location != 'World'],
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
    
# Scatter Plot - Correlations

df['Vaccinations per Capita'] = round(df['total_vaccinations']/df['population'],3).replace(np.nan,0)

st.subheader(f'Relationship between Vaccination per Capita and Macroenvironmental Index on {sel_date}')

scatterplot = alt.Chart(df).mark_circle(size=60).encode(
    alt.X('variable', title=sel_index),
    alt.Y('Vaccinations per Capita', title='Cumulated Total Vaccinations per Capita'),
    color='Continent',
    opacity=opacity,
    tooltip=[alt.Tooltip('location', title="Country"), alt.Tooltip('variable', title=sel_index), 'Vaccinations per Capita']
).add_selection(hover)

regression = alt.Chart(df).mark_circle(size=60).encode(
    alt.X('variable', title=sel_index),
    y='Vaccinations per Capita').transform_regression('variable','Vaccinations per Capita').mark_line()  
   
                         
st.altair_chart((scatterplot + regression).configure_scale(bandPaddingInner=.1).interactive(), use_container_width=True)
   
   
