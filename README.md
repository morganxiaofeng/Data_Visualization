# COVID-19 Progress: Evolution of Emerging Cases & Vaccination in 2021
Interactive Dashboard of COVID-19 Progress: Evolution of Emerging Cases & Vaccination in 2021 employing [Streamlit](https://www.streamlit.io) module .
You can try [here](https://share.streamlit.io/morganxiaofeng/data_visualization/main/app.py).

## Primary objectives
* Basic options for users to choose
  * Continent
  * Macroenvironmental Index
  * Date
* Display the evolution of cases and vaccinations with stacked area charts, line charts and heatmaps.
* Draw a Choropleth of geographical heatmap of the macroenvironmental index
* Draw scatter plots of relationships between vaccinations per capita and indexes

## Data sources and helpful resources
* [locations](https://github.com/owid/covid-19-data/blob/master/public/data/vaccinations/locations.csv)
* [Global vaccinations and cases](https://github.com/owid/covid-19-data/blob/master/public/data/owid-covid-data.csv)

  
## Selected modules used
  * [Altair](http://altair-viz.github.io/): Altair chart module used to draw heatmap (`streamlit.altair_chart`)
  * [Pydeck](http://pydeck.gl/): Pydeck mapping module used to draw Choropleth/PolygonLayer (`streamlit.pydeck_chart`)
  

