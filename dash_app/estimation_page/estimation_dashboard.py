
import pandas as pd
import plotly.express as px
from dash import dcc, html, callback, Output, Input

# Mapbox token (hidden)
mapbox_token = "pk.eyJ1Ijoic3RvY2hhc3RpYzEwMTciLCJhIjoiY20ydmJpMzhrMGIwdDJqb2NoZGt5emw0YiJ9.QJXmXS_gHKVxDV4mVkmIOw"
px.set_mapbox_access_token(mapbox_token)

# Load metadata for stations and airports
df_station = pd.read_csv("ncei-lcd-list-2024.csv")
df_airport = pd.read_csv("airports-list-us.csv")
years = [2018, 2019, 2020, 2021, 2022, 2023, 2024]
months = [
    {'label': 'January', 'value': 'Jan'},
    {'label': 'November', 'value': 'Nov'},
    {'label': 'December', 'value': 'Dec'}
]

# Available metrics for the time series
metrics = [
    # Hourly measurements
    {'label': 'Hourly Dry Bulb Temperature', 'value': 'HourlyDryBulbTemperature'},      # 17401 files
    {'label': 'Hourly Wind Speed', 'value': 'HourlyWindSpeed'},                         # 16762 files
    {'label': 'Hourly Wind Direction', 'value': 'HourlyWindDirection'},                 # 16639 files
    {'label': 'Hourly Dew Point Temperature', 'value': 'HourlyDewPointTemperature'},    # 14540 files
    {'label': 'Hourly Relative Humidity', 'value': 'HourlyRelativeHumidity'},           # 14531 files
    {'label': 'Hourly Visibility', 'value': 'HourlyVisibility'},                        # 14417 files
    {'label': 'Hourly Station Pressure', 'value': 'HourlyStationPressure'},             # 10686 files
    {'label': 'Hourly Wet Bulb Temperature', 'value': 'HourlyWetBulbTemperature'},      # 9625 files
    {'label': 'Hourly Sky Conditions', 'value': 'HourlySkyConditions'},                 # 8519 files
]

# Color scale
weather_color_scale = px.colors.cyclical.IceFire

# Layout
estimation_layout = html.Div([
    html.H1("Enhanced US Map: Weather Stations & Airports", style={
        'text-align': 'center', 'color': '#333', 'margin': '20px 0', 'font-family': 'Arial, sans-serif'
    }),
    
    # Control panel
    html.Div([
        html.Div([
            html.Label('Select Data Type', style={'font-weight': 'bold', 'margin-bottom': '8px', 'display': 'block'}),
            dcc.Dropdown(
                id='data-selector',
                options=[
                    {'label': 'Weather Stations', 'value': 'stations'},
                    {'label': 'Airports', 'value': 'airports'},
                ],
                value='stations',
                className='custom-dropdown'
            )
        ], style={'margin-bottom': '25px'}),
        
        html.Div([
            html.Label('Map Style', style={'font-weight': 'bold', 'margin-bottom': '8px', 'display': 'block'}),
            dcc.Dropdown(
                id='mapbox-style-selector',
                options=[
                    {'label': 'Streets', 'value': 'streets-v11'},
                    {'label': 'Satellite', 'value': 'satellite-v9'},
                    {'label': 'Dark', 'value': 'dark-v10'},
                    {'label': 'Light', 'value': 'light-v10'},
                    {'label': 'Outdoors', 'value': 'outdoors-v11'},
                ],
                value='streets-v11',
                className='custom-dropdown'
            )
        ], style={'margin-bottom': '25px'}),

        html.Div([
            html.Label('Select Year', style={'font-weight': 'bold', 'margin-bottom': '8px', 'display': 'block'}),
            dcc.Dropdown(
                id='year-selector',
                options=[{'label': str(year), 'value': year} for year in years],
                value=2024,
                className='custom-dropdown'
            )
        ], style={'margin-bottom': '25px'}),

        html.Div([
            html.Label('Select Month', style={'font-weight': 'bold', 'margin-bottom': '8px', 'display': 'block'}),
            dcc.Dropdown(
                id='month-selector',
                options=months,
                value='Jan',
                className='custom-dropdown'
            )
        ], style={'margin-bottom': '25px'}),

        html.Div([
            html.Label('Select Metric', style={'font-weight': 'bold', 'margin-bottom': '8px', 'display': 'block'}),
            dcc.Dropdown(
                id='metric-selector',
                options=metrics,
                value='HourlyDewPointTemperature',
                className='custom-dropdown',
                style={'max-width': '100%'}
            )
        ], style={'margin-bottom': '25px'}),
        
    ], style={
        'width': '320px', 'float': 'left', 'padding': '30px', 'background': '#f8f9fa', 
        'border-radius': '10px', 'box-shadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '20px',
        'font-family': 'Arial, sans-serif'
    }),
    
    # Map display
    html.Div([
        dcc.Graph(id="enhanced-map", config={"scrollZoom": True}, style={'width': '100%', 'height': '80vh'})
    ], style={'margin-left': '360px', 'padding': '20px'}),

    # Time-series plot display with initial empty state
    html.Div([
        html.H2("Weather Data Time-Series", style={'text-align': 'center'}),
        html.Div(id="timeseries-container", children=[
            dcc.Graph(id="timeseries-plot", style={'width': '90%', 'margin': '0 auto'})
        ], style={'display': 'none'})
    ]),
])

@callback(
    Output("enhanced-map", "figure"),
    Output("timeseries-container", "style"),
    Output("timeseries-plot", "figure"),
    [Input("data-selector", "value"),
     Input("mapbox-style-selector", "value"),
     Input("year-selector", "value"),
     Input("month-selector", "value"),
     Input("metric-selector", "value"),
     Input("enhanced-map", "clickData")]
)
def update_maps(selected_data, mapbox_style, selected_year, selected_month, selected_metric, click_data):
    # Create base map figure
    fig = create_map_figure(selected_data, mapbox_style)
    
    # Initialize time series visibility and figure
    timeseries_style = {'display': 'none'}
    timeseries_fig = px.line()  # Empty figure as default
    
    # Update time series if a station is clicked
    if click_data and selected_data == 'stations':
        try:
            station_name = click_data['points'][0]['hovertext']
            timeseries_fig = create_timeseries_plot(
                station_name, 
                selected_year, 
                selected_month, 
                selected_metric
            )
            timeseries_style = {'display': 'block'}
        except Exception as e:
            print(f"Error creating time series plot: {e}")
            timeseries_style = {'display': 'none'}
    
    return fig, timeseries_style, timeseries_fig

def create_map_figure(selected_data, mapbox_style):
    if selected_data == 'stations':
        fig = create_enhanced_weather_map(df_station)
    else:
        fig = create_enhanced_airport_map(df_airport)
    
    fig.update_layout(
        mapbox=dict(
            style=f"mapbox://styles/mapbox/{mapbox_style}",
            accesstoken=mapbox_token,
            zoom=3.5,
            center={"lat": 37.0902, "lon": -95.7129},
        ),
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        showlegend=False
    )
    
    return fig

def create_enhanced_weather_map(df):
    return px.scatter_mapbox(
        df,
        lat="latitude",
        lon="longitude",
        hover_name="station",
        hover_data={"station_name": True, "elevation": True, "admin1": True, "admin2": True},
        color="elevation",
        color_continuous_scale=weather_color_scale,
        range_color=[df['elevation'].min(), df['elevation'].max()],
    ).update_traces(marker=dict(size=10, opacity=0.7))

def create_enhanced_airport_map(df):
    return px.scatter_mapbox(
        df,
        lat="LATITUDE",
        lon="LONGITUDE",
        hover_name="AIRPORT",
        hover_data={"DISPLAY_AIRPORT_NAME": True, "City": True, "AIRPORT_STATE_NAME": True},
        color="AIRPORT_STATE_CODE",
    ).update_traces(marker=dict(size=10, opacity=0.7))

def create_timeseries_plot(station, year, month, metric):
    try:
        # Define the GCS file path for the selected year and station
        file_path = f"gs://airport-weather-data/ncei-lcd/{year}/{station}.csv"
        
        # Load CSV directly from GCS
        df = pd.read_csv(file_path, storage_options={"token": "flights-weather-project-f94d306bee1f.json"})
        
        # Convert DATE to datetime
        df['DATE'] = pd.to_datetime(df['DATE'])
        
        # Filter for selected month
        df = df[df['DATE'].dt.strftime('%b') == month]
        
        # Get the metric's label for the plot title
        metric_label = next((item['label'] for item in metrics if item['value'] == metric), metric)
        
        # Create the time series plot
        fig = px.line(
            df, 
            x=df['DATE'].dt.to_pydatetime(),
            y=metric,
            title=f"{metric_label} - {station} ({month} {year})",
            labels={metric: metric_label}
        )
        
        # Improve the layout
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title=metric_label,
            hovermode='x unified',
            template='plotly_white'
        )
        
        return fig
    except Exception as e:
        print(f"Error in create_timeseries_plot: {e}")
        # Return an empty figure with an error message
        return px.line(title=f"Error loading data for station {station}")
    