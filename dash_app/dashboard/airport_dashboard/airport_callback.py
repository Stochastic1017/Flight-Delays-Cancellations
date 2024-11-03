
import pandas as pd
from dash import callback, Output, State, Input, html
import plotly.graph_objects as go
import plotly.express as px
from .airport_helpers import create_airport_map_figure, create_airport_dashboard

# Mapbox token setup
mapbox_token = "pk.eyJ1Ijoic3RvY2hhc3RpYzEwMTciLCJhIjoiY20ydmJpMzhrMGIwdDJqb2NoZGt5emw0YiJ9.QJXmXS_gHKVxDV4mVkmIOw"
px.set_mapbox_access_token(mapbox_token)

# Load airport data
df_airport = pd.read_csv("airports-list-us.csv")

# Default plot function for unselected states/cities
def create_default_plot():
    fig = go.Figure()
    fig.update_layout(
        plot_bgcolor="black",
        paper_bgcolor="black",
        title="Station Time-Series Overview",
        height=600,
        width=800,
        template="plotly_dark"
    )
    return fig

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
    # Filter city options based on the selected state
    if selected_state:
        city_options = [{'label': city, 'value': city} 
                        for city in df_airport[df_airport['State'] == selected_state]['City'].unique()]
    else:
        city_options = [{'label': city, 'value': city} 
                        for city in df_airport['City'].unique()]

    # Filter DataFrame based on selected state and city
    filtered_df = df_airport
    if selected_state:
        filtered_df = filtered_df[filtered_df['State'] == selected_state]
    if selected_city:
        filtered_df = filtered_df[filtered_df['City'] == selected_city]

    # Create the map figure
    fig = create_airport_map_figure(mapbox_style, marker_size, marker_opacity, filtered_df)

    # Get station information
    station_info = None
    if click_data:
        station_id = click_data['points'][0]['hovertext']
        station_df = filtered_df[filtered_df['AIRPORT_ID'] == station_id]
        station_info = station_df.iloc[0].to_dict() if not station_df.empty else None

    # Generate table based on station_info
    if station_info:
        coords = f"({station_info['LATITUDE']}, {station_info['LONGITUDE']})" if pd.notna(station_info['LATITUDE']) and pd.notna(station_info['LONGITUDE']) else "N/A"
        station_info_table = html.Table([
            html.Tr([html.Th("Airport Info")]),
            html.Tr([html.Td("Name:"), html.Td(station_info["DISPLAY_AIRPORT_NAME"])]),
            html.Tr([html.Td("Airport:"), html.Td(station_info["AIRPORT"])]),
            html.Tr([html.Td("Coordinates:"), html.Td(coords)]),
            html.Tr([html.Td("State:"), html.Td(station_info["AIRPORT_STATE_NAME"])]),
            html.Tr([html.Td("City:"), html.Td(station_info["DISPLAY_CITY_MARKET_NAME_FULL"])]),
        ])
    else:
        station_info_table = html.Table([
            html.Tr([html.Th("No Station Selected")])
        ])

    return city_options, fig, station_info_table

@callback(
    Output("airport-timeseries-plot", "figure"),
    [Input("airport-update-plot-button", "n_clicks")],
    [State("airport-enhanced-map", "clickData"),
     State("airport-year-selector", "value"),
     State("airport-month-selector", "value")]
)
def update_visualization(n_clicks, click_data, selected_year, selected_month):
    
    month = {"January": 1, "November": 11, "December": 12}[selected_month]

    if not n_clicks or not click_data:
        fig = create_default_plot()
        fig.add_annotation(
            text="Please select a station on the map first",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14)
        )
        return fig

    # Extract selected station details
    station_id = click_data['points'][0]['hovertext']
    station_info = df_airport[df_airport['AIRPORT_ID'] == station_id].iloc[0]

    return create_airport_dashboard(station_id, station_info['AIRPORT'], selected_year, month)
