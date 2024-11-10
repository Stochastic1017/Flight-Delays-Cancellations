
import pandas as pd
import plotly.graph_objects as go
from dash import callback, Output, Input, State, html
import plotly.express as px
from .weather_helpers import (create_weather_map_figure, create_timeseries_plot)

# Mapbox token (hidden)
mapbox_token = "pk.eyJ1Ijoic3RvY2hhc3RpYzEwMTciLCJhIjoiY20ydmJpMzhrMGIwdDJqb2NoZGt5emw0YiJ9.QJXmXS_gHKVxDV4mVkmIOw"
px.set_mapbox_access_token(mapbox_token)

# Load airport metadata
weather_metdata = f"gs://airport-weather-data/ncei-lcd-list-us.csv"
df_station = pd.read_csv(weather_metdata, storage_options={"token": "flights-weather-project-f94d306bee1f.json"})

# Default plot function for unselected states/cities
def create_default_plot():
    fig = go.Figure()
    fig.update_layout(
        plot_bgcolor="black",
        paper_bgcolor="black",
        title="Station Time-Series Overview",
        height=1060,
        width=1510,
        template="plotly_dark"
    )
    return fig

@callback(
    [Output("weather-city-selector", "options"),
     Output("weather-enhanced-map", "figure"),
     Output("weather-station-info-table", "children")],
    [Input("weather-mapbox-style-selector", "value"),
     Input("weather-marker-size", "value"),
     Input("weather-marker-opacity", "value"),
     Input("weather-color-scale-selector", "value"),
     Input("weather-state-selector", "value"),
     Input("weather-city-selector", "value"),
     Input("weather-enhanced-map", "clickData")]
)
def update_map_and_station_info(mapbox_style, marker_size, marker_opacity, weather_color_scale, selected_state, selected_city, click_data):
    
    # City options based on selected state
    if selected_state:
        city_options = [{'label': city, 'value': city} 
                        for city in df_station[df_station['state'] == selected_state]['names'].unique()]
    else:
        city_options = [{'label': city, 'value': city} 
                        for city in df_station['names'].unique()]

    # Filter data based on state and city
    filtered_df = df_station
    if selected_state:
        filtered_df = filtered_df[filtered_df['state'] == selected_state]
    if selected_city:
        filtered_df = filtered_df[filtered_df['names'] == selected_city]

    # Default map zoom and center
    center = {"lat": 37.0902, "lon": -95.7129}
    zoom = 3.5

    # Check for click data to set zoom and center to the clicked station
    if click_data:
        station_name = click_data['points'][0]['hovertext']
        station_df = filtered_df[filtered_df['station'] == station_name]
        if not station_df.empty:
            station_info = station_df.iloc[0].to_dict()
            center = {"lat": station_info["latitude"], "lon": station_info["longitude"]}
            zoom = 10  # Closer zoom level after clicking

    fig = create_weather_map_figure(
        mapbox_style,
        marker_size,
        marker_opacity,
        weather_color_scale,
        filtered_df,
        center=center,
        zoom=zoom
    )

    # Create station info table
    if click_data and station_info:
        station_info_table = html.Table([
            html.Tr([html.Th("Station Info")]),
            html.Tr([html.Td("Name:"), html.Td(station_info["station_name"])]),
            html.Tr([html.Td("Coordinates:"), html.Td(f"({station_info['latitude']}, {station_info['longitude']})")]),
            html.Tr([html.Td("Location:"), html.Td(station_info["names"])]),
            html.Tr([html.Td("Admin 1:"), html.Td(station_info["admin1"])]),
            html.Tr([html.Td("Admin 2:"), html.Td(station_info["admin2"])])
        ])
    else:
        station_info_table = html.Table([
            html.Tr([html.Th("No Station Selected")])
        ])

    return city_options, fig, station_info_table

@callback(
    Output("weather-timeseries-plot", "figure"),
    [Input("weather-update-plot-button", "n_clicks")],
    [State("weather-enhanced-map", "clickData"),
     State("weather-year-selector", "value"),
     State("weather-metric-selector", "value")]
)
def update_timeseries(n_clicks, click_data, selected_year, selected_metric):
    if (n_clicks is None) or (not click_data):
        fig = create_default_plot()
        fig.add_annotation(
            text="Please select a station on the map first",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14)
        )
        return fig

    station = click_data['points'][0]['hovertext']
    station_info = df_station[df_station['station'] == station].iloc[0]
    title_info = f"Station: {station_info['station_name']} ({station}) - {station_info['names']}, {station_info['state']}"

    return create_timeseries_plot(station, selected_year, selected_metric, title_info)
