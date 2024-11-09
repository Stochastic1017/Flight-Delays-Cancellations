
import gcsfs
import pandas as pd
import numpy as np
from dash import callback, Output, State, Input, html
import plotly.graph_objects as go
import plotly.express as px
from .airport_helpers import create_airport_map_figure, create_delay_plots

# Initialize Google Cloud Storage FileSystem
fs = gcsfs.GCSFileSystem(project='Flights-Weather-Project', token='flights-weather-project-f94d306bee1f.json')

# Mapbox token setup
mapbox_token = "pk.eyJ1Ijoic3RvY2hhc3RpYzEwMTciLCJhIjoiY20ydmJpMzhrMGIwdDJqb2NoZGt5emw0YiJ9.QJXmXS_gHKVxDV4mVkmIOw"
px.set_mapbox_access_token(mapbox_token)

# Load airport metadata
airport_metdata = f"gs://airport-weather-data/airports-list-us.csv"
df_airport = pd.read_csv(airport_metdata, storage_options={"token": "flights-weather-project-f94d306bee1f.json"})

# Load airport metadata
weather_metdata = f"gs://airport-weather-data/closest_airport_weather.csv"
df_weather = pd.read_csv(weather_metdata, storage_options={"token": "flights-weather-project-f94d306bee1f.json"})

# Default plot function for unselected states/cities
def create_default_plot():
    fig = go.Figure()
    fig.update_layout(
        plot_bgcolor="black",
        paper_bgcolor="black",
        title="",
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
     Input("airport-enhanced-map", "clickData"),
     Input("n_closest_slider", "value"),
     Input("max_weather_dist", "value")]
)
def update_map_and_station_info(mapbox_style, marker_size, marker_opacity, selected_state, selected_city, click_data, n_closest, max_distance):

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

    # Create the map figure with base airport markers
    fig = create_airport_map_figure(mapbox_style, marker_size, marker_opacity, filtered_df)

    # Initialize airport_info and default map center/zoom
    airport_info = None
    center = dict(lat=39.8283, lon=-98.5795)  # Center of USA
    zoom = 3  # Default zoom level

    # If an airport is clicked, find and display the closest weather stations
    if click_data:
        airport_id = click_data['points'][0]['hovertext']
        
        # Retrieve airport info from df_weather to ensure matching columns
        if not df_weather[df_weather['AIRPORT_ID'] == airport_id].empty:
            airport_info = df_weather[df_weather['AIRPORT_ID'] == airport_id].iloc[0]
            
            # Parse the AIRPORT_COORDINATES if it is a string
            try:
                airport_lat, airport_lon = eval(airport_info['AIRPORT_COORDINATES'])
                # Update center and zoom for the clicked airport
                center = dict(lat=airport_lat, lon=airport_lon)
                zoom = 8  # Closer zoom level for selected airport

            except Exception as e:
                print(f"Error parsing coordinates: {e}")
                airport_lat, airport_lon = None, None

            # Filter weather stations within the maximum distance ceiling
            filtered_stations = df_weather[(df_weather['AIRPORT_ID'] == airport_id) & 
                                           (df_weather['DISTANCE_KM'] <= max_distance)]
            # Get the n closest weather stations within the filtered range
            closest_stations = filtered_stations.nsmallest(n_closest, 'DISTANCE_KM')

            # Add enhanced markers for weather stations with hover data
            fig.add_trace(go.Scattermapbox(
                lat=[eval(coord)[0] for coord in closest_stations['WEATHER_COORDINATES']],
                lon=[eval(coord)[1] for coord in closest_stations['WEATHER_COORDINATES']],
                mode='markers',
                marker=go.scattermapbox.Marker(
                    size=15,
                    opacity=1.0,
                    color='black'
                ),
                hovertext=closest_stations.apply(
                    lambda x: f"Station: {x['WEATHER_STATION_NAME']}<br>" +
                            f"Distance: {x['DISTANCE_KM']:.1f} km<br>" +
                            f"Elevation: {x['WEATHER_ELEVATION']} m",
                    axis=1
                ),
                name='Weather Stations',
                hoverinfo='text'  # Ensure hoverinfo is set to text
            ))

            # Draw enhanced connection lines with gradients and hover info
            for _, station in closest_stations.iterrows():
                weather_lat, weather_lon = eval(station['WEATHER_COORDINATES'])
                
                # Create gradient effect with multiple segments
                num_segments = 20
                lat_points = np.linspace(airport_lat, weather_lat, num_segments)
                lon_points = np.linspace(airport_lon, weather_lon, num_segments)
                
                # Calculate opacity gradient
                opacities = np.linspace(0.2, 0.8, num_segments-1)
                
                # Add segments with decreasing opacity
                for i in range(len(lat_points)-1):
                    fig.add_trace(go.Scattermapbox(
                        lat=[lat_points[i], lat_points[i+1]],
                        lon=[lon_points[i], lon_points[i+1]],
                        mode='lines',
                        line=dict(
                            width=2,
                            color=f'rgba(0, 0, 0, {opacities[i]})'
                        ),
                        hovertext=f"Connection to {station['WEATHER_STATION_NAME']}<br>" +
                                  f"Distance: {station['DISTANCE_KM']:.1f} km",
                        hoverinfo='text',
                        showlegend=False
                    ))

    # Update the map layout with new center and zoom
    fig.update_layout(
        mapbox=dict(
            center=center,
            zoom=zoom
        )
    )

    # Generate station info table if airport_info is set
    if airport_info is not None:
        station_info_table = html.Table([
            html.Tr([html.Th("Airport Info")]),
            html.Tr([html.Td("Name:"), html.Td(airport_info.get("AIRPORT_DISPLAY_NAME", "N/A"))]),
            html.Tr([html.Td("Airport:"), html.Td(airport_info.get("AIRPORT_NAME", "N/A"))]),
            html.Tr([html.Td("Coordinates:"), html.Td(f"({airport_lat}, {airport_lon})")]),
            html.Tr([html.Td("State:"), html.Td(airport_info.get("AIRPORT_STATE", "N/A"))]),
            html.Tr([html.Td("City:"), html.Td(airport_info.get("AIRPORT_CITY", "N/A"))]),
            html.Tr([html.Td("Country:"), html.Td(airport_info.get("AIRPORT_COUNTRY", "N/A"))]),
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
     State("airport-plot-selector", "value")]
)
def update_visualization(n_clicks, click_data, selected_year, selected_plot_type):
    # Validate input: button click, map selection, year, and plot type
    if not n_clicks or not click_data:
        fig = create_default_plot()
        fig.add_annotation(
            text="Please select an airport on the map and choose data of interest.",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14)
        )
        return fig

    if not selected_year or not selected_plot_type:
        fig = create_default_plot()
        fig.add_annotation(
            text="Please select a year and data of interest.",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14)
        )
        return fig

    # Retrieve airport ID and information from the map click data
    airport_id = click_data['points'][0]['hovertext']
    try:
        airport_info = df_airport[df_airport['AIRPORT_ID'] == airport_id].iloc[0]
        airport_name = airport_info['DISPLAY_AIRPORT_NAME']
        airport_city = airport_info['City']
        airport_state = airport_info['State']
        title_info = f"{airport_name} ({airport_id}) - {airport_city}, {airport_state}"
    except IndexError:
        # Handle the case where the airport ID is not found in the dataframe
        fig = create_default_plot()
        fig.add_annotation(
            text="Selected airport data not available.",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color="red")
        )
        return fig

    if selected_plot_type == "Delay Viz":
        return create_delay_plots(airport_id, selected_year, title_info=title_info)
