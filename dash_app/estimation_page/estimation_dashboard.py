
import pandas as pd
import plotly.express as px
from dash import dcc, html, callback, Output, Input

# Load station and airport data with updated columns
df_station = pd.read_csv("https://raw.githubusercontent.com/Stochastic1017/Flight-Delays-Cancellations/refs/heads/main/stats/metadata/ghcnd-stations-us.csv")
df_airport = pd.read_csv("https://raw.githubusercontent.com/Stochastic1017/Flight-Delays-Cancellations/refs/heads/main/stats/metadata/airports-list.csv")

# Filter for US airports only
df_airport = df_airport[df_airport["AIRPORT_COUNTRY_CODE_ISO"] == "US"].reset_index(drop=True)

# Define a custom color sequence combining multiple distinct color palettes
colors = (
    px.colors.qualitative.Set1 +
    px.colors.qualitative.Set2 +
    px.colors.qualitative.Set3 +
    px.colors.qualitative.Pastel1 +
    px.colors.qualitative.Bold +
    px.colors.qualitative.Safe +
    px.colors.qualitative.Pastel2 +
    px.colors.cyclical.IceFire +
    px.colors.cyclical.Phase +
    px.colors.cyclical.Edge +
    px.colors.cyclical.HSV
)

# Define the layout with a dropdown for data selection
estimation_layout = html.Div([
    html.H1("US Map: Weather Stations & Airports", style={'text-align': 'center', 'color': '#333'}),
    html.Div([
        dcc.Dropdown(
            id='data-selector',
            options=[
                {'label': 'Weather Stations', 'value': 'stations'},
                {'label': 'Airports', 'value': 'airports'}
            ],
            value='stations',  # Default value
            style={'width': '300px', 'margin': '20px auto'}
        )
    ], style={'text-align': 'center'}),
    dcc.Graph(
        id="station-map",
        config={"scrollZoom": True},
        style={'width': '80vw', 'height': '80vh'}
    )
])

@callback(
    Output("station-map", "figure"),
    [Input("data-selector", "value")]
)
def update_map(selected_data):
    if selected_data == 'stations':
        df = df_station
        hover_data = {"Elevation": True, "State": True}
        color_column = "Elevation"
        hover_name = "Station ID"
        marker_size = 8
        
        # Create the map figure with continuous color scale for stations
        fig = px.scatter_mapbox(
            df,
            lat="Latitude",
            lon="Longitude",
            hover_name=hover_name,
            hover_data=hover_data,
            color=color_column,
            color_continuous_scale=px.colors.cyclical.IceFire,
            zoom=3.5,
            center={"lat": 37.0902, "lon": -95.7129}
        )
    else:
        df = df_airport
        hover_data = {
            "DISPLAY_AIRPORT_NAME": True,
            "DISPLAY_AIRPORT_CITY_NAME_FULL": True,
            "AIRPORT_STATE_NAME": True,
            "AIRPORT_STATE_CODE": True,
            "AIRPORT_WAC": True,
            "AIRPORT_COUNTRY_NAME": True
        }
        color_column = "AIRPORT_STATE_CODE"
        hover_name = "AIRPORT"
        marker_size = 10
        
        # Create the map figure with discrete colors for airports
        fig = px.scatter_mapbox(
            df,
            lat="LATITUDE",
            lon="LONGITUDE",
            hover_name=hover_name,
            hover_data=hover_data,
            color=color_column,
            color_discrete_sequence=colors,  # Use our custom color sequence
            zoom=3.5,
            center={"lat": 37.0902, "lon": -95.7129}
        )

    # Update marker size and map layout
    fig.update_traces(marker=dict(size=marker_size))
    fig.update_layout(
        mapbox_style="carto-positron",
        margin={"r": 10, "t": 10, "l": 10, "b": 10}
    )
    
    return fig