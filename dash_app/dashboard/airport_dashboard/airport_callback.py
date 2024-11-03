

import pandas as pd
from dash import callback, Output, Input, html
import plotly.express as px
from .airport_helpers import create_airport_map_figure

# Mapbox token (hidden)
mapbox_token = "pk.eyJ1Ijoic3RvY2hhc3RpYzEwMTciLCJhIjoiY20ydmJpMzhrMGIwdDJqb2NoZGt5emw0YiJ9.QJXmXS_gHKVxDV4mVkmIOw"
px.set_mapbox_access_token(mapbox_token)

# Load data
df_airport = pd.read_csv("filtered-airports-list-us.csv")

@callback(
    [Output("airport-city-selector", "options"),
     Output("airport-enhanced-map", "figure"),
     Output("airport-info-table", "children")],
    [Input("airport-mapbox-style-selector", "value"),
     Input("airport-marker-size", "value"),
     Input("airport-marker-opacity", "value"),
     Input("airport-state-selector", "value"),
     Input("airport-city-selector", "value"),
     Input("airport-enhanced-map", "clickData")]
)
def update_map_and_station_info(mapbox_style, marker_size, marker_opacity, selected_state, selected_city, click_data):
    # Filter cities based on state selection
    if selected_state:
        city_options = [{'label': city, 'value': city} 
                        for city in df_airport[df_airport['State'] == selected_state]['City'].unique()]
    else:
        city_options = [{'label': city, 'value': city} 
                        for city in df_airport['City'].unique()]

    # Filter stations based on state and city selection
    filtered_df = df_airport
    if selected_state:
        filtered_df = filtered_df[filtered_df['State'] == selected_state]
    if selected_city:
        filtered_df = filtered_df[filtered_df['City'] == selected_city]

    # Create map figure
    fig = create_airport_map_figure(mapbox_style, marker_size, marker_opacity, filtered_df)

    # Get station information with error handling
    station_info = None
    if click_data:
        station_name = click_data['points'][0]['hovertext']
        station_df = filtered_df[filtered_df['AIRPORT_ID'] == station_name]
        station_info = station_df.iloc[0].to_dict() if not station_df.empty else None
    else:
        station_info = filtered_df.iloc[0].to_dict() if not filtered_df.empty else None

    if station_info:
        station_info_table = html.Table([
            html.Tr([html.Th("Airport Info")]),
            html.Tr([html.Td("Name:"), html.Td(station_info["DISPLAY_AIRPORT_NAME"])]),
            html.Tr([html.Td("Airport:"), html.Td(station_info["AIRPORT"])]),
            html.Tr([html.Td("Coordinates:"), html.Td(f"{station_info['LATITUDE']}, {station_info['LONGITUDE']}")]),
            html.Tr([html.Td("State:"), html.Td(station_info["AIRPORT_STATE_NAME"])]),
            html.Tr([html.Td("City:"), html.Td(station_info["DISPLAY_CITY_MARKET_NAME_FULL"])]),
        ])

    else:
        station_info_table = html.Table([
            html.Tr([html.Th("No Airport Selected")]),
            html.Tr([html.Td("Please select a station from the map")])
        ])

    return city_options, fig, station_info_table
