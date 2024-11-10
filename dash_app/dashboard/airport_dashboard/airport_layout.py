
import gcsfs
import pandas as pd
from dash import dcc, html, Output, Input, callback

# Initialize Google Cloud Storage FileSystem
fs = gcsfs.GCSFileSystem(project='Flights-Weather-Project', token='flights-weather-project-f94d306bee1f.json')

# Load airport metadata
airport_metdata = f"gs://airport-weather-data/airports-list-us.csv"
df_airport = pd.read_csv(airport_metdata, storage_options={"token": "flights-weather-project-f94d306bee1f.json"})

# Unique states and cities for dropdown filtering
states = [{'label': state, 'value': state} 
          for state in df_airport['State'].unique()]

years = [2018, 2019, 2020, 2021, 2022, 2023, 2024]
months = {"January": 1, "November": 11, "December": 12}

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

airport_color_scales = [
    {'label': 'Viridis', 'value': 'Viridis'},
    {'label': 'Plasma', 'value': 'Plasma'},
    {'label': 'Cividis', 'value': 'Cividis'},
    {'label': 'Inferno', 'value': 'Inferno'},
    {'label': 'Magma', 'value': 'Magma'},
    {'label': 'Turbo', 'value': 'Turbo'},
    {'label': 'Rainbow', 'value': 'Rainbow'},
    {'label': 'Bluered', 'value': 'Bluered'},
    {'label': 'Electric', 'value': 'Electric'}
]

gradient_types = [
    {'label': 'No Gradient', 'value': ''},
    {'label': 'Cancellations', 'value': 'CancellationRate'},
    {'label': 'Average Arrival Delay', 'value': 'AvgArrivalDelay'},
    {'label': 'Average Departure Delay', 'value': 'AvgDepartureDelay'},
    {'label': 'Average Total Flight Delay', 'value': 'AvgTotalFlightDelay'},
    {'label': 'Average Taxi Delay', 'value': 'AvgTaxiDelay'}
]

# Define the layout for the airport dashboard
airport_dashboard_layout = html.Div([
    html.Div([
        html.H3("Control Panel", className="section-title"),

        # Location Filters
        html.Div([
            html.Label('Location Filters', className="label"),
            dcc.Dropdown(
                id='airport-state-selector',
                options=states,
                placeholder="Select State",
                className="dropdown",
                clearable=True
            ),
            dcc.Dropdown(
                id='airport-city-selector',
                placeholder="Select City",
                className="dropdown",
                clearable=True
            )
        ], className="control-panel-section", style={'margin-bottom': '10px'}),

        # Marker Settings
        html.Div([
            html.Label('Marker Size', className="label"),
            dcc.Slider(
                id='airport-marker-size',
                min=5,
                max=25,
                step=1,
                value=10,
                marks={i: str(i) for i in range(5, 26, 10)},
                className='custom-slider'
            ),
            html.Label('Opacity', className="label"),
            dcc.Slider(
                id='airport-marker-opacity',
                min=0.1,
                max=1.0,
                step=0.1,
                value=0.7,
                marks={i/10: f"{i/10:.1f}" for i in range(1, 11, 2)},
                className='custom-slider'
            )
        ], className="control-panel-section", style={'margin-bottom': '10px'}),

        # Weather Station Settings
        html.Div([
            html.Label('Weather Stations', className="label"),
            dcc.Slider(
                id='n_closest_slider',
                min=1,
                max=10,
                step=1,
                value=5,
                marks={i: str(i) for i in range(1, 11, 2)},
                className='custom-slider'
            ),
            html.Label('Max Distance', className="label"),
            dcc.Slider(
                id='max_weather_dist',
                min=1,
                max=100,
                step=5,
                value=50,
                marks={i: str(i) for i in range(1, 101, 20)},
                className='custom-slider'
            ),
            dcc.Checklist(
                id='binary_disp_weather_station',
                options=[{'label': 'Show Weather Stations', 'value': 'visible'}],
                value=['visible'],
                inline=True,
                className="control-panel-section"
            )
        ], className="control-panel-section", style={'margin-bottom': '10px'}),

                # Visualization Settings
        html.Div([
            html.Label('Visualization Settings', className="label"),
            dcc.Dropdown(
                id='airport-mapbox-style-selector',
                options=map_options,
                value='navigation-day-v1',
                className="dropdown",
                clearable=False
            ),
            dcc.Dropdown(
                id='gradient-marker-col',
                options=gradient_types,
                placeholder="Select Gradient",
                value='',
                className="dropdown",
                clearable=False
            ),
            dcc.Dropdown(
                id='airport-color-scale-selector',
                options=airport_color_scales,
                value='Viridis',
                className="dropdown",
                clearable=False
            )
        ], className="control-panel-section", style={'margin-bottom': '10px'}),

    ], className="control-panel", style={'width': '15%', 'float': 'left', 'padding': '10px', 'margin-right': '20px'}),

    html.Div([
        # Map and Info Sections with slight margin adjustments
        dcc.Graph(
            id="airport-enhanced-map",
            config={"scrollZoom": True},
            style={'height': '45vh', 'margin-bottom': '20px'}
        ),
        html.Div(id="airport-info-table", className="station-info-table", style={'margin-bottom': '20px'}),
        html.Div(id="airport-station-info-table", className="station-info-table", style={'margin-bottom': '20px'}),

        # Data Exploration Settings
        html.Div([
            html.Label('Data Exploration', className="label"),
            dcc.Dropdown(
                id='airport-plot-selector',
                options=[
                    {'label': "Departure vs Arrival Delay", 'value': "Delay Viz"},
                    {'label': "Cancellations", 'value': "Cancel Viz"}
                ],
                value="Delay Viz",
                placeholder="Select Data of Interest",
                className="dropdown"
            ),
            dcc.Dropdown(
                id='airport-year-selector',
                options=[{'label': str(year), 'value': year} for year in years],
                value=years[0],
                placeholder="Select Year",
                className="dropdown"
            ),
            dcc.Dropdown(
                id='airport-month-selector',
                placeholder="Select Month",
                value=1,
                className="dropdown"
            ),
            html.Button("Update Plot", id="airport-update-plot-button", className="update-plot-button", style={'margin-top': '10px'})
        ], className="time-series-settings-section", style={'margin-bottom': '20px'}),

        # Time Series Plot
        dcc.Graph(
            id="airport-timeseries-plot",
            style={'height': '80vh'}
        )
    ], className="main-content", style={'width': '75%', 'float': 'right', 'padding': '10px'})
], style={'max-width': '3000px', 'margin': '20px auto', 'padding-top': '20px', 'padding-left': '20px', 'display': 'flex', 'flex-wrap': 'wrap'})

# Update month dropdown options based on the selected year
@callback(
    Output('airport-month-selector', 'options'),
    Input('airport-year-selector', 'value')
)
def update_month_options(selected_year):
    if selected_year == 2024:
        # Only include January for 2024
        available_months = {"January": 1}
    else:
        # Include January, November, and December for other years
        available_months = months
    
    return [{'label': k, 'value': v} for k, v in available_months.items()]