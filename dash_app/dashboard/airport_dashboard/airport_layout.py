

import pandas as pd
from dash import dcc, html

# Load data
df_airport = pd.read_csv("filtered-airports-list-us.csv")

# Unique states and cities for dropdown filtering
states = [{'label': state, 'value': state} 
          for state in df_airport['State'].unique()]

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
                        html.Div(id="airport-info-table", className="airport-info-table", style={'margin-bottom': '20px'}),
                    ], className="airport-info-and-settings-container", style={'width': '75%', 'float': 'right', 'padding': '10px'}),

                    html.Div([
                        dcc.Graph(
                            id="airport-timeseries-plot",
                            style={'height': '110vh'}
                        )
                    ], className="timeseries-container", style={'margin-top': '20px', 'clear': 'both'})
                ], className="main-content", style={'width': '75%', 'float': 'right', 'padding': '10px'})
            ], className="dashboard-container", style={'display': 'flex', 'flex-wrap': 'wrap'})
        ], style={'max-width': '3000px', 'margin': '0 auto'})
