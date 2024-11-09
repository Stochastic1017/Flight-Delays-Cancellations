
import gcsfs
import pandas as pd
from dash import dcc, html

# Initialize Google Cloud Storage FileSystem
fs = gcsfs.GCSFileSystem(project='Flights-Weather-Project', token='flights-weather-project-f94d306bee1f.json')

# Load airport metadata
airport_metdata = f"gs://airport-weather-data/airports-list-us.csv"
df_airport = pd.read_csv(airport_metdata, storage_options={"token": "flights-weather-project-f94d306bee1f.json"})

# Unique states and cities for dropdown filtering
states = [{'label': state, 'value': state} 
          for state in df_airport['State'].unique()]

years = [2018, 2019, 2020, 2021, 2022, 2023, 2024]

map_options = [
    {'label': 'Streets', 'value': 'streets-v11'},
    {'label': 'Satellite', 'value': 'satellite-v9'},
    {'label': 'Outdoors', 'value': 'outdoors-v11'},
    {'label': 'Light', 'value': 'light-v10'},
    {'label': 'Dark', 'value': 'dark-v10'},
    {'label': 'Satellite Streets', 'value': 'satellite-streets-v11'},
    {'label': 'Navigation Day', 'value': 'navigation-day-v1'},
    {'label': 'Navigation Night', 'value': 'navigation-night-v1'}
]

# Define the layout for the airport dashboard
airport_dashboard_layout = html.Div([
            html.Div([
                # Control panel and layout elements
                html.Div([
                    html.H3("Control Panel", className="section-title"),
                    
                    html.Div([
                        html.Label('Visualization Settings', className="label"),
                        dcc.Dropdown(
                            id='airport-mapbox-style-selector',
                            options=map_options,
                            value='streets-v11',
                            className="dropdown",
                            clearable=False
                        ),
                    ], className="control-panel-section"),

                    html.Div([
                        html.Label('Marker Size', className="label"),
                        dcc.Slider(
                            id='airport-marker-size',
                            min=5,
                            max=25,
                            step=1,
                            value=10,
                            marks={i: str(i) for i in range(5, 26, 5)},
                            className='custom-slider'
                        ),
                        html.Label('Marker Opacity', className="label"),
                        dcc.Slider(
                            id='airport-marker-opacity',
                            min=0.1,
                            max=1.0,
                            step=0.1,
                            value=0.7,
                            marks={i/10: str(i/10) for i in range(1, 11)},
                            className='custom-slider'
                        )
                    ], className="control-panel-section"),

                    html.Div([
                        html.Label('Closest Weather Stations', className="label"),
                        dcc.Slider(
                            id='n_closest_slider',
                            min=1,
                            max=10,
                            step=1,
                            value=5,
                            marks={i: str(i) for i in range(1, 11)},
                            tooltip={"placement": "bottom", "always_visible": True}
                        )
                    ], className="control-panel-section"),

                    html.Div([
                        html.Label('Maximum Weather Station Distance', className="label"),
                        dcc.Slider(
                            id='max_weather_dist',
                            min=1,
                            max=100,
                            step=5,
                            value=50,
                            marks={i: str(i) for i in range(1, 100, 20)},
                            tooltip={"placement": "bottom", "always_visible": True}
                        )
                    ], className="control-panel-section"),

                    html.Div([
                        html.Label('Location Filters', className="label"),
                        dcc.Dropdown(
                            id='airport-state-selector',
                            options=states,
                            placeholder="Select State",
                            className="dropdown",
                            clearable=True,
                            multi=False
                        ),
                        dcc.Dropdown(
                            id='airport-city-selector',
                            placeholder="Select City",
                            className="dropdown",
                            clearable=True,
                            multi=False
                        )
                    ], className="control-panel-section")
                ], className="control-panel", style={'width': '15%', 'float': 'left', 'padding': '10px'}),

                html.Div([
                    html.Div([
                        dcc.Graph(
                            id="airport-enhanced-map",
                            config={"scrollZoom": True},
                            style={'height': '50vh'}
                        )
                    ], className="map-container", style={'margin-bottom': '20px'}),

                    html.Div([
                        html.Div(id="airport-info-table", className="station-info-table", style={'margin-bottom': '20px'}),
                    ], className="airport-info-and-settings-container", style={'width': '75%', 'float': 'right', 'padding': '10px'}),

                    html.Div([
                        html.Div(id="airport-station-info-table", className="station-info-table", style={'margin-bottom': '20px'}),
                        html.Div([
                            html.Label('Data Exploration Settings', className="label"),
                            dcc.Dropdown(
                                id='airport-year-selector',
                                options=[{'label': str(year), 'value': year} for year in years],
                                value=years[0],
                                placeholder="Select Year",
                                className="dropdown time-series-settings-dropdown",
                                searchable=True,
                                clearable=False
                            ),
                            dcc.Dropdown(
                                id='airport-plot-selector',
                                options=[{'label': "Departure delay vs Arrival delay Visualizations", 'value': "Delay Viz"}],
                                value="Delay Viz",
                                placeholder="Select Data of Interest",
                                className="dropdown time-series-settings-dropdown",
                                searchable=True,
                                clearable=False
                            ),
                            html.Button("Update Plot", id="airport-update-plot-button", className="update-plot-button", style={'margin-top': '10px'})
                        ], className="time-series-settings-section", style={'margin-top': '20px'})
                    ], className="station-info-and-settings-container", style={'width': '75%', 'float': 'right', 'padding': '10px'}),

                    html.Div([
                        dcc.Graph(
                            id="airport-timeseries-plot",
                            style={'height': '110vh'}
                        )
                    ], className="timeseries-container", style={'margin-top': '20px', 'clear': 'both'})
                ], className="main-content", style={'width': '75%', 'float': 'right', 'padding': '10px'})
            ], className="dashboard-container", style={'display': 'flex', 'flex-wrap': 'wrap'})
        ], style={'max-width': '3000px', 'margin': '0 auto'})
