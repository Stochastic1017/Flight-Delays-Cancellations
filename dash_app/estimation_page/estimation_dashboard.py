
import pandas as pd
import plotly.express as px
from dash import dcc, html, callback, Output, Input

# Load station and airport data with updated columns
df_station = pd.read_csv("https://raw.githubusercontent.com/Stochastic1017/Flight-Delays-Cancellations/refs/heads/main/stats/metadata/ghcnd-stations-us.csv")
df_airport = pd.read_csv("https://raw.githubusercontent.com/Stochastic1017/Flight-Delays-Cancellations/refs/heads/main/stats/metadata/airports-list.csv")

# Filter for US airports only
df_airport = df_airport[df_airport["AIRPORT_COUNTRY_CODE_ISO"] == "US"].reset_index(drop=True)

# List of states for dropdown, starting with "All"
states = ["All"] + sorted(df_airport['AIRPORT_STATE_CODE'].dropna().unique())

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

# Create a color mapping for consistent state colors
unique_states = df_airport['AIRPORT_STATE_CODE'].unique()
state_color_map = {state: colors[i % len(colors)] for i, state in enumerate(unique_states)}

# Set fixed color range for Elevation in weather stations
elevation_min = df_station['Elevation'].min()
elevation_max = df_station['Elevation'].max()

# Define the layout with a dropdown for data selection and state selection
estimation_layout = html.Div([
    html.H1("US Map: Weather Stations & Airports", style={'text-align': 'center', 'color': '#333'}),
    
    # Dropdowns for data type and state selection
    html.Div([
        dcc.Dropdown(
            id='data-selector',
            options=[
                {'label': 'Weather Stations', 'value': 'stations'},
                {'label': 'Airports', 'value': 'airports'}
            ],
            value='stations',  # Default value
            style={'width': '300px', 'margin': '10px auto'}
        ),
        dcc.Dropdown(
            id='state-selector',
            options=[{'label': state, 'value': state} for state in states],
            value='All',  # Default value
            placeholder="Select a state",
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

@callback(
    Output("station-map", "figure"),
    [Input("data-selector", "value"), Input("state-selector", "value")]
)

def update_map(selected_data, selected_state):
    
    # Select data source based on dropdown selection
    if selected_data == 'stations':
        df = df_station
        hover_data = {"Elevation": True, "State": True}
        color_column = "Elevation"
        hover_name = "Station ID"
        marker_size = 8
        color_scale = px.colors.cyclical.IceFire
        color_range = [elevation_min, elevation_max]
    
    else:
        df = df_airport
        hover_data = {
            "DISPLAY_AIRPORT_NAME": True,
            "DISPLAY_AIRPORT_CITY_NAME_FULL": True,
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
    if selected_state != "All":
        if selected_data == 'stations':
            df = df[df['State'] == selected_state]
        else:
            df = df[df['AIRPORT_STATE_CODE'] == selected_state]

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
        center={"lat": 37.0902, "lon": -95.7129}
    )

    # Update marker size
    fig.update_traces(marker=dict(size=marker_size))

    # Update map layout
    fig.update_layout(
        mapbox_style="carto-positron",
        margin={"r": 10, "t": 10, "l": 10, "b": 10}
    )
    
    return fig
