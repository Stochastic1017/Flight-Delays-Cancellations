
import pandas as pd
import plotly.express as px
from dash import dcc, html, callback, Output, Input

# Load station and airport data with updated columns
df_station = pd.read_csv("https://raw.githubusercontent.com/Stochastic1017/Flight-Delays-Cancellations/refs/heads/main/stats/metadata/ghcnd-stations-us.csv")
df_airport = pd.read_csv("https://raw.githubusercontent.com/Stochastic1017/Flight-Delays-Cancellations/refs/heads/main/stats/metadata/airports-list-us.csv")
df_station.loc[df_station["Elevation"] <= -999, "Elevation"] = 0

# List of states for dropdown
states = sorted(df_airport['AIRPORT_STATE_CODE'].dropna().unique())

# Define a custom color sequence and assign colors per state
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
unique_states = df_airport['AIRPORT_STATE_CODE'].unique()
state_color_map = {state: colors[i % len(colors)] for i, state in enumerate(unique_states)}

# Set fixed color range for Elevation in weather stations
elevation_min = df_station['Elevation'].min()
elevation_max = df_station['Elevation'].max()

# Define the layout with dropdowns for data selection, state selection, and city selection
estimation_layout = html.Div([
    html.H1("US Map: Weather Stations & Airports", style={'text-align': 'center', 'color': '#333'}),
    
    # Dropdowns for data type, state, and city selection
    html.Div([
        dcc.Dropdown(
            id='data-selector',
            options=[
                {'label': 'Weather Stations', 'value': 'stations'},
                {'label': 'Airports', 'value': 'airports'}
            ],
            clearable=False,
            value='stations',
            style={'width': '300px', 'margin': '10px auto'}
        ),
        dcc.Dropdown(
            id='state-selector',
            options=[{'label': state, 'value': state} for state in states],
            placeholder="Select a state",
            style={'width': '300px', 'margin': '10px auto'}
        ),
        dcc.Dropdown(
            id='city-selector',
            placeholder="Select a city",
            style={'width': '300px', 'margin': '10px auto'}
        )
    ], style={'text-align': 'center'}),
    
    # Map display
    dcc.Graph(
        id="station-map",
        config={"scrollZoom": True},
        style={'width': '80vw', 'height': '80vh'}
    )
])

# Callback to populate city dropdown based on selected data type and state
@callback(
    Output("city-selector", "options"),
    [Input("data-selector", "value"), Input("state-selector", "value")]
)
def update_city_dropdown(selected_data, selected_state):
    # Filter data based on selection
    if selected_data == 'stations':
        df = df_station
        city_column = "City"
    else:
        df = df_airport
        city_column = "City"

    # Filter by state if a specific state is selected
    if selected_state:
        df = df[df['State'] == selected_state if selected_data == 'stations' else df['AIRPORT_STATE_CODE'] == selected_state]
    
    # Extract unique cities
    cities = sorted(df[city_column].dropna().unique())
    return [{'label': city, 'value': city} for city in cities]

# Callback to update map based on dropdown selections
@callback(
    Output("station-map", "figure"),
    [Input("data-selector", "value"), Input("state-selector", "value"), Input("city-selector", "value")]
)
def update_map(selected_data, selected_state, selected_city):
    # Select data source based on dropdown selection
    if selected_data == 'stations':
        df = df_station
        hover_data = {
            "Station Name": True,
            "Station ID": True,
            "Latitude": True,
            "Longitude": True,
            "Elevation": True, 
            "State": True,
            "City": True,
            "County": True,
            }
        color_column = "Elevation"
        hover_name = "Station ID"
        marker_size = 8
        color_scale = "Inferno"
        color_range = [elevation_min, elevation_max]  # Fixed color
    
    else:
        df = df_airport
        hover_data = {
            "DISPLAY_AIRPORT_NAME": True,
            "City": True,
            "AIRPORT_STATE_NAME": True,
            "AIRPORT_STATE_CODE": True,
            "AIRPORT_WAC": True
        }
        hover_name = "AIRPORT"
        marker_size = 10
        color_range = None

        # Map state colors to each airport based on predefined state colors
        df['StateColor'] = df['AIRPORT_STATE_CODE'].map(state_color_map)
        color_column = "AIRPORT_STATE_CODE"  # Set the color column to mapped state colors

    # Apply state filter if a specific state is selected
    if selected_state:
        df = df[df['State'] == selected_state] if selected_data == 'stations' else df[df['AIRPORT_STATE_CODE'] == selected_state]
    
    # Apply city filter if a specific city is selected
    if selected_city:
        df = df[df['City'] == selected_city] if selected_data == 'stations' else df[df['City'] == selected_city]

    # Create the map figure
    fig = px.scatter_mapbox(
        df,
        lat="Latitude" if selected_data == 'stations' else "LATITUDE",
        lon="Longitude" if selected_data == 'stations' else "LONGITUDE",
        hover_name=hover_name,
        hover_data=hover_data,
        color=color_column,
        color_discrete_map=state_color_map if selected_data == 'airports' else None,
        color_continuous_scale=color_scale if selected_data == 'stations' else None,
        zoom=3.5,
        center={"lat": 37.0902, "lon": -95.7129},
        opacity=0.5
    )

    # Update marker size
    fig.update_traces(marker=dict(size=marker_size))

    # Update map layout
    fig.update_layout(
        mapbox_style="carto-positron",
        margin={"r": 10, "t": 10, "l": 10, "b": 10}
    )
    
    return fig
