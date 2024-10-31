
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import dcc, html, callback, Output, Input
import numpy as np
from scipy import stats
import warnings
from operator import itemgetter

# Mapbox token (hidden)
mapbox_token = "pk.eyJ1Ijoic3RvY2hhc3RpYzEwMTciLCJhIjoiY20ydmJpMzhrMGIwdDJqb2NoZGt5emw0YiJ9.QJXmXS_gHKVxDV4mVkmIOw"
px.set_mapbox_access_token(mapbox_token)

# Load metadata for stations
df_station = pd.read_csv("ncei-lcd-list-us.csv")
years = [2018, 2019, 2020, 2021, 2022, 2023, 2024]

# Unique states and cities for dropdown filtering
states = [{'label': state, 'value': state} for state in df_station['state'].unique()]

# Available metrics for the time series
metrics = [
    {'label': 'Hourly Dry Bulb Temperature', 'value': 'HourlyDryBulbTemperature'},
    {'label': 'Hourly Wind Speed', 'value': 'HourlyWindSpeed'},
    {'label': 'Hourly Wind Direction', 'value': 'HourlyWindDirection'},
    {'label': 'Hourly Dew Point Temperature', 'value': 'HourlyDewPointTemperature'},
    {'label': 'Hourly Relative Humidity', 'value': 'HourlyRelativeHumidity'},
    {'label': 'Hourly Visibility', 'value': 'HourlyVisibility'},
    {'label': 'Hourly Station Pressure', 'value': 'HourlyStationPressure'},
    {'label': 'Hourly Wet Bulb Temperature', 'value': 'HourlyWetBulbTemperature'},
    {'label': 'Hourly Sky Conditions', 'value': 'HourlySkyConditions'},
]

# Color scale
weather_color_scale = "Inferno"

# Layout
estimation_layout = html.Div([
    html.H1("Enhanced US Map:\nStudying Weather Stations", style={
        'text-align': 'center', 'color': '#333', 'margin': '20px 0', 'font-family': 'Arial, sans-serif', 'white-space': 'pre'
    }),

    # Control panel
    html.Div([
        html.Div([
            html.Label('Map Style', style={'font-weight': 'bold', 'margin-bottom': '8px', 'display': 'block'}),
            dcc.Dropdown(
                id='mapbox-style-selector',
                options=[
                    {'label': 'Streets', 'value': 'streets-v11'},
                    {'label': 'Satellite', 'value': 'satellite-v9'},
                    {'label': 'Dark', 'value': 'dark-v10'},
                    {'label': 'Light', 'value': 'light-v10'},
                ],
                value='streets-v11',
                className='custom-dropdown'
            )
        ], style={'margin-bottom': '25px'}),

        html.Div([
            html.Label('Filter by State', style={'font-weight': 'bold', 'margin-bottom': '8px', 'display': 'block'}),
            dcc.Dropdown(
                id='state-selector',
                options=states,
                className='custom-dropdown'
            )
        ], style={'margin-bottom': '25px'}),

        html.Div([
            html.Label('Filter by City', style={'font-weight': 'bold', 'margin-bottom': '8px', 'display': 'block'}),
            dcc.Dropdown(
                id='city-selector',
                className='custom-dropdown'
            )
        ], style={'margin-bottom': '25px'}),

        html.Div([
            html.Label('Marker Size', style={'font-weight': 'bold', 'margin-bottom': '8px', 'display': 'block'}),
            dcc.Slider(
                id='marker-size',
                min=5,
                max=25,
                step=1,
                value=10,
                marks={i: str(i) for i in range(5, 26, 5)},
                className='custom-slider'
            )
        ], style={'margin-bottom': '25px'}),

        html.Div([
            html.Label('Marker Opacity', style={'font-weight': 'bold', 'margin-bottom': '8px', 'display': 'block'}),
            dcc.Slider(
                id='marker-opacity',
                min=0.1,
                max=1.0,
                step=0.1,
                value=0.7,
                marks={i/10: str(i/10) for i in range(1, 11)},
                className='custom-slider'
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

    # Time-series plot display with metric and year selection
    html.Div([
        html.H2("Weather Data Time-Series", style={'text-align': 'center'}),
        
        html.Div([
            html.Div([
                html.Label('Select Year', style={'font-weight': 'bold', 'margin-bottom': '8px', 'display': 'block'}),
                dcc.Dropdown(
                    id='year-selector',
                    options=[{'label': str(year), 'value': year} for year in years],
                    value=2018,
                    className='custom-dropdown'
                )
            ], style={'margin-bottom': '25px'}),

            html.Div([
                html.Label('Select Metric', style={'font-weight': 'bold', 'margin-bottom': '8px', 'display': 'block'}),
                dcc.Dropdown(
                    id='metric-selector',
                    options=metrics,
                    value='HourlyDryBulbTemperature',
                    className='custom-dropdown'
                )
            ], style={'margin-bottom': '25px'}),
            
        ], style={'width': '320px', 'margin': '0 auto', 'padding': '20px', 'background': '#f8f9fa', 
                  'border-radius': '10px', 'box-shadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin-top': '20px',
                  'font-family': 'Arial, sans-serif'}),
        
        html.Div(id="timeseries-container", children=[
            dcc.Graph(id="timeseries-plot", style={'width': '95%', 'height': '85vh', 'margin': '0 auto'})
        ], style={'display': 'none'})
    ]),
])

@callback(
    Output("city-selector", "options"),
    Output("enhanced-map", "figure"),
    Output("timeseries-container", "style"),
    Output("timeseries-plot", "figure"),
    [Input("mapbox-style-selector", "value"),
     Input("marker-size", "value"),
     Input("marker-opacity", "value"),
     Input("year-selector", "value"),
     Input("metric-selector", "value"),
     Input("state-selector", "value"),
     Input("city-selector", "value"),
     Input("enhanced-map", "clickData")]
)
def update_maps(mapbox_style, marker_size, marker_opacity, selected_year, selected_metric, selected_state, selected_city, click_data):
    # Filter cities based on state selection
    if selected_state:
        city_options = [{'label': city, 'value': city} for city in df_station[df_station['state'] == selected_state]['names'].unique()]
    else:
        city_options = [{'label': city, 'value': city} for city in df_station['names'].unique()]

    # Filter stations by state and city
    filtered_df = df_station
    if selected_state:
        filtered_df = filtered_df[filtered_df['state'] == selected_state]
    if selected_city:
        filtered_df = filtered_df[filtered_df['names'] == selected_city]

    # Create map figure
    fig = create_map_figure(mapbox_style, marker_size, marker_opacity, filtered_df)
    
    # Initialize time series visibility and figure
    timeseries_style = {'display': 'none'}
    timeseries_fig = px.line()  # Empty figure as default
    
    # Check if a point on the map has been clicked
    if click_data:
        try:
            station_name = click_data['points'][0]['hovertext']
            station_info = filtered_df[filtered_df['station'] == station_name].iloc[0].to_dict()
            title_info = " | ".join(itemgetter("station_name", "coords", "names", "admin1", "admin2")(station_info))
            
            timeseries_fig = create_timeseries_plot(station_name, selected_year, selected_metric, title_info)
            timeseries_style = {'display': 'block'}
        except Exception as e:
            print(f"Error creating time series plot: {e}")
            timeseries_style = {'display': 'none'}
    
    return city_options, fig, timeseries_style, timeseries_fig

def create_map_figure(mapbox_style, marker_size, marker_opacity, filtered_df):
    fig = create_enhanced_weather_map(filtered_df, marker_size, marker_opacity)
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

def create_enhanced_weather_map(df, marker_size, marker_opacity):
    return px.scatter_mapbox(
        df,
        lat="latitude",
        lon="longitude",
        hover_name="station",
        hover_data={"station_name": True, "elevation": True, "admin1": True, "admin2": True},
        color="elevation",
        color_continuous_scale=weather_color_scale,
        range_color=[df['elevation'].min(), df['elevation'].max()],
    ).update_traces(marker=dict(size=marker_size, opacity=marker_opacity))

def create_timeseries_plot(station, year, metric, title_info):
    try:
        warnings.filterwarnings('ignore', category=FutureWarning)
        
        file_path = f"gs://airport-weather-data/ncei-lcd/{station}.csv"
        df = pd.read_csv(file_path, storage_options={"token": "flights-weather-project-f94d306bee1f.json"}, low_memory=False)
        
        df["DATE"] = pd.to_datetime(df["DATE"], errors='coerce')
        df[metric] = pd.to_numeric(df[metric], errors='coerce')
        
        months_to_plot = [1, 11, 12]
        filtered_df = df[df["DATE"].dt.month.isin(months_to_plot) & (df["DATE"].dt.year == year)].copy()
        
        if filtered_df.empty:
            raise ValueError(f"No data available for {station} in {year}")
        
        fig = make_subplots(
            rows=3, cols=2,
            shared_xaxes=False,
            column_widths=[0.7, 0.3],  # Allocate more space to line plots
            horizontal_spacing=0.05,   # Increase space between subplots
            vertical_spacing=0.2,
            subplot_titles=[
                "January Time Series", "January Distribution",
                "November Time Series", "November Distribution",
                "December Time Series", "December Distribution"
            ],
            specs=[[{"type": "scatter"}, {"type": "xy"}],
                   [{"type": "scatter"}, {"type": "xy"}],
                   [{"type": "scatter"}, {"type": "xy"}]]
        )
        
        colors = {1: '#1f77b4', 11: '#2ca02c', 12: '#d62728'}
        
        for i, month in enumerate(months_to_plot, 1):
            month_df = filtered_df[filtered_df["DATE"].dt.month == month].copy()
            
            if not month_df.empty:
                kde_y = month_df[metric].dropna().astype(float)
                
                if len(kde_y) > 1:
                    plot_dates = np.array(month_df["DATE"].dt.to_pydatetime())
                    
                    kde = stats.gaussian_kde(kde_y)
                    kde_x = np.linspace(kde_y.min(), kde_y.max(), 100)
                    kde_points = kde(kde_x)
                    
                    fig.add_trace(
                        go.Scatter(
                            x=plot_dates,
                            y=kde_y,
                            mode="lines",
                            line=dict(color=colors[month], width=2)
                        ),
                        row=i, col=1
                    )
                    
                    month_start = pd.Timestamp(year=year, month=month, day=1)
                    month_end = month_start + pd.offsets.MonthEnd(1)
                    fig.update_xaxes(range=[month_start, month_end], row=i, col=1)
                    
                    fig.add_trace(
                        go.Histogram(
                            y=kde_y,
                            histnorm='probability density',
                            showlegend=False,
                            marker=dict(color=colors[month], opacity=0.3),
                            nbinsy=30
                        ),
                        row=i, col=2
                    )
                    
                    fig.add_trace(
                        go.Scatter(
                            x=kde_points,
                            y=kde_x,
                            mode="lines",
                            showlegend=False,
                            line=dict(color=colors[month], width=2)
                        ),
                        row=i, col=2
                    )
        
        fig.update_layout(
            title=dict(
                text=title_info,
                font=dict(size=20),
                y=0.98,
                x=0.5
            ),
            height=1000,
            width=1400,
            template="plotly_white",
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            hovermode='closest',
            margin=dict(t=100, b=50, l=50, r=50)
        )
        
        for i in range(1, 4):
            fig.update_xaxes(title_text="Date", gridcolor='lightgray', row=i, col=1)
            fig.update_yaxes(title_text=metric if i == 2 else "", gridcolor='lightgray', row=i, col=1)
            fig.update_xaxes(title_text="Density", gridcolor='lightgray', row=i, col=2)
            fig.update_yaxes(title_text=metric if i == 2 else "", gridcolor='lightgray', row=i, col=2)
        
        return fig
    
    except Exception as e:
        print(f"Error: {str(e)}")
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error loading data for station {station}:<br>{str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color="red")
        )
        fig.update_layout(
            title=f"Error - {station} ({year})",
            template="plotly_white"
        )
        return fig
