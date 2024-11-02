
import pandas as pd
import plotly.graph_objects as go
from dash import callback, Output, Input, State, html
import plotly.express as px
from .helpers import create_map_figure, create_timeseries_plot

# Mapbox token (hidden)
mapbox_token = "pk.eyJ1Ijoic3RvY2hhc3RpYzEwMTciLCJhIjoiY20ydmJpMzhrMGIwdDJqb2NoZGt5emw0YiJ9.QJXmXS_gHKVxDV4mVkmIOw"
px.set_mapbox_access_token(mapbox_token)

# Load data
df_station = pd.read_csv("ncei-lcd-list-us.csv")

@callback(
    [Output("city-selector", "options"),
     Output("enhanced-map", "figure"),
     Output("station-info-table", "children")],
    [Input("mapbox-style-selector", "value"),
     Input("marker-size", "value"),
     Input("marker-opacity", "value"),
     Input("weather-color-scale-selector", "value"),
     Input("state-selector", "value"),
     Input("city-selector", "value"),
     Input("enhanced-map", "clickData")]
)
def update_map_and_station_info(mapbox_style, marker_size, marker_opacity, weather_color_scale, selected_state, selected_city, click_data):
    # Filter cities based on state selection
    if selected_state:
        city_options = [{'label': city, 'value': city} for city in df_station[df_station['state'] == selected_state]['names'].unique()]
    else:
        city_options = [{'label': city, 'value': city} for city in df_station['names'].unique()]

    # Filter stations based on state and city selection
    filtered_df = df_station
    if selected_state:
        filtered_df = filtered_df[filtered_df['state'] == selected_state]
    if selected_city:
        filtered_df = filtered_df[filtered_df['names'] == selected_city]

    # Create map figure
    fig = create_map_figure(mapbox_style, marker_size, marker_opacity, weather_color_scale, filtered_df)

    # Get station information with error handling
    station_info = None
    if click_data:
        station_name = click_data['points'][0]['hovertext']
        station_df = filtered_df[filtered_df['station'] == station_name]
        station_info = station_df.iloc[0].to_dict() if not station_df.empty else None
    else:
        station_info = filtered_df.iloc[0].to_dict() if not filtered_df.empty else None

    if station_info:
        station_info_table = html.Table([
            html.Tr([html.Th("Station Info")]),
            html.Tr([html.Td("Name:"), html.Td(station_info["station_name"])]),
            html.Tr([html.Td("Coordinates:"), html.Td(station_info["coords"])]),
            html.Tr([html.Td("Location:"), html.Td(station_info["names"])]),
            html.Tr([html.Td("Admin 1:"), html.Td(station_info["admin1"])]),
            html.Tr([html.Td("Admin 2:"), html.Td(station_info["admin2"])])
        ])
    else:
        station_info_table = html.Table([
            html.Tr([html.Th("No Station Selected")]),
            html.Tr([html.Td("Please select a station from the map")])
        ])

    return city_options, fig, station_info_table

@callback(
    Output("timeseries-plot", "figure"),
    [Input("update-plot-button", "n_clicks")],
    [State("enhanced-map", "clickData"),
     State("year-selector", "value"),
     State("metric-selector", "value")]
)
def update_timeseries(n_clicks, click_data, selected_year, selected_metric):
    if n_clicks is None:
        return go.Figure()

    if not click_data:
        fig = go.Figure()
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
