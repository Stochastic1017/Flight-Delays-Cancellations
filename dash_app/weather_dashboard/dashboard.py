
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import dcc, html, callback, Output, Input, State
import numpy as np
from scipy import stats
import warnings

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
]

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

weather_color_scales = [
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

weather_dashboard_layout = html.Div([
    
    # Compact, Sticky Control Panel on the Side
    html.Div([
        html.H3("Control Panel", className="section-title"),
        
        # Visualization Settings Section
        html.Div([
            html.Label('Visualization Settings', className="label"),
            dcc.Dropdown(
                id='mapbox-style-selector',
                options=map_options,
                value='streets-v11',
                className="dropdown",
                clearable=False
            ),
            html.Label('Color Scale', className="label"),
            dcc.Dropdown(
                id='weather-color-scale-selector',
                options=weather_color_scales,
                value='Viridis',
                className="dropdown",
                clearable=False
            )
        ], className="control-panel-section"),

        # Marker Size and Opacity Section
        html.Div([
            html.Label('Marker Size', className="label"),
            dcc.Slider(
                id='marker-size',
                min=5,
                max=25,
                step=1,
                value=10,
                marks={i: str(i) for i in range(5, 26, 5)},
                className='custom-slider'
            ),
            html.Label('Marker Opacity', className="label"),
            dcc.Slider(
                id='marker-opacity',
                min=0.1,
                max=1.0,
                step=0.1,
                value=0.7,
                marks={i/10: str(i/10) for i in range(1, 11)},
                className='custom-slider'
            ),
        ], className="control-panel-section"),

        # Location Filters Section
        html.Div([
            html.Label('Location Filters', className="label"),
            dcc.Dropdown(
                id='state-selector',
                options=states,
                placeholder="Select State",
                className="dropdown",
                clearable=True,
                multi=False
            ),
            dcc.Dropdown(
                id='city-selector',
                placeholder="Select City",
                className="dropdown",
                clearable=True,
                multi=False
            ),
        ], className="control-panel-section"),
      
    ], className="control-panel"),

    # Main Content Area
    html.Div([

        # Map Container
        html.Div([
            dcc.Graph(
                id="enhanced-map",
                config={"scrollZoom": True},
                style={'height': '50vh'}
            )
        ], className="map-container"),

        # Station Info Table and Update Button
        html.Div([
            html.Div(id="station-info-table", className="station-info-table"),
        ], className="station-info-section"),

        # Add this new section near the station info table
        html.Div([
            # Station Info Table
            html.Div(id="station-info-table", className="station-info-table"),

            # Time Series Settings Section
            html.Div([
                html.Label('Time Series Settings', className="label"),
                dcc.Dropdown(
                    id='year-selector',
                    options=[{'label': str(year), 'value': year} for year in years],
                    value=2018,
                    placeholder="Select Year",
                    className="dropdown time-series-settings-dropdown",
                    searchable=True,
                    clearable=False
                ),
                dcc.Dropdown(
                    id='metric-selector',
                    options=metrics,
                    value='HourlyDryBulbTemperature',
                    placeholder="Select Metric",
                    className="dropdown time-series-settings-dropdown",
                    searchable=True,
                    clearable=False
                ),
                html.Button("Update Plot", id="update-plot-button", className="update-plot-button"),
            ], className="time-series-settings-section"),
        ], className="station-info-and-settings-container"),

        # Time-Series Plot
        html.Div([
            dcc.Graph(
                id="timeseries-plot",
                style={'height': '50vh'}
            )
        ], className="timeseries-container"),

    ], className="main-content")
], className="dashboard-container")

@callback(
    [Output("city-selector", "options"),
     Output("enhanced-map", "figure"),
     Output("station-info-table", "children")],
    [Input("mapbox-style-selector", "value"),
     Input("marker-size", "value"),
     Input("marker-opacity", "value"),
     Input("weather-color-scale-selector", "value"),
     Input("state-selector", "value"),
     Input("city-selector", "value"),
     Input("enhanced-map", "clickData")]
)
def update_map_and_station_info(mapbox_style, marker_size, marker_opacity, weather_color_scale, selected_state, selected_city, click_data):
    # Filter cities based on state selection
    if selected_state:
        city_options = [{'label': city, 'value': city} for city in df_station[df_station['state'] == selected_state]['names'].unique()]
    else:
        city_options = [{'label': city, 'value': city} for city in df_station['names'].unique()]

    # Filter stations based on state and city selection
    filtered_df = df_station
    if selected_state:
        filtered_df = filtered_df[filtered_df['state'] == selected_state]
    if selected_city:
        filtered_df = filtered_df[filtered_df['names'] == selected_city]

    # Create map figure with the chosen color scale
    fig = create_map_figure(mapbox_style, marker_size, marker_opacity, weather_color_scale, filtered_df)
    
    # Get station information with error handling
    if click_data:
        station_name = click_data['points'][0]['hovertext']
        station_df = filtered_df[filtered_df['station'] == station_name]
        
        if len(station_df) > 0:
            station_info = station_df.iloc[0].to_dict()
        else:
            station_info = filtered_df.iloc[0].to_dict() if not filtered_df.empty else None
    else:
        station_info = filtered_df.iloc[0].to_dict() if not filtered_df.empty else None

    if station_info:
        station_info_table = html.Table([
            html.Tr([html.Th("Station Info")]),
            html.Tr([html.Td("Name:"), html.Td(station_info["station_name"])]),
            html.Tr([html.Td("Coordinates:"), html.Td(station_info["coords"])]),
            html.Tr([html.Td("Location:"), html.Td(station_info["names"])]),
            html.Tr([html.Td("Admin 1:"), html.Td(station_info["admin1"])]),
            html.Tr([html.Td("Admin 2:"), html.Td(station_info["admin2"])])
        ])
    else:
        station_info_table = html.Table([
            html.Tr([html.Th("No Station Selected")]),
            html.Tr([html.Td("Please select a station from the map")])
        ])

    return city_options, fig, station_info_table

@callback(
    Output("timeseries-plot", "figure"),
    [Input("update-plot-button", "n_clicks")],
    [State("enhanced-map", "clickData"),
     State("year-selector", "value"),
     State("metric-selector", "value")]
)
def update_timeseries(n_clicks, click_data, selected_year, selected_metric):
    if n_clicks is None:
        # Return empty figure on initial load
        return go.Figure()
    
    if not click_data:
        # Return figure with message if no station is selected
        fig = go.Figure()
        fig.add_annotation(
            text="Please select a station on the map first",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14)
        )
        return fig
    
    # Get selected station from click data
    station = click_data['points'][0]['hovertext']
    
    # Get station info for the title
    station_info = df_station[df_station['station'] == station].iloc[0]
    title_info = f"Station: {station_info['station_name']} ({station}) - {station_info['names']}, {station_info['state']}"
    
    # Create and return the time series plot
    return create_timeseries_plot(station, selected_year, selected_metric, title_info)

def create_map_figure(mapbox_style, marker_size, marker_opacity, weather_color_scale, filtered_df):
    fig = create_enhanced_weather_map(filtered_df, marker_size, marker_opacity, weather_color_scale)
    fig.update_layout(
        mapbox=dict(
            style=f"mapbox://styles/mapbox/{mapbox_style}",
            accesstoken=mapbox_token,
            zoom=3.5,
            center={"lat": 37.0902, "lon": -95.7129},
        ),
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        showlegend=False,
        legend=dict(
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor="chocolate",
            borderwidth=1,
            font=dict(size=12, color="chocolate")
        )
    )
    return fig

def create_enhanced_weather_map(df, marker_size, marker_opacity, weather_color_scale):
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
        
        months_to_plot = [1, 11, 12]  # January, November, December
        filtered_df = df[df["DATE"].dt.month.isin(months_to_plot) & (df["DATE"].dt.year == year)].copy()
        
        if filtered_df.empty:
            raise ValueError(f"No data available for {station} in {year}")
        
        fig = make_subplots(
            rows=3, cols=3,
            shared_xaxes=False,
            column_widths=[0.7, 0.3, 0.3],
            vertical_spacing=0.15,
            horizontal_spacing=0.05,
            subplot_titles=[
                "January Time Series", "January Distribution", "January Stats",
                "November Time Series", "November Distribution", "November Stats",
                "December Time Series", "December Distribution", "December Stats"
            ],
            specs=[[{"type": "scatter"}, {"type": "xy"}, {"type": "table"}],
                   [{"type": "scatter"}, {"type": "xy"}, {"type": "table"}],
                   [{"type": "scatter"}, {"type": "xy"}, {"type": "table"}]]
        )
        
        colors = {1: '#1f77b4', 11: '#2ca02c', 12: '#d62728'}
        
        for i, month in enumerate(months_to_plot, 1):
            month_df = filtered_df[filtered_df["DATE"].dt.month == month].copy()
            
            if not month_df.empty:
                kde_y = month_df[metric].dropna().astype(float)
                mean_y = kde_y.mean()
                std_y = kde_y.std()
                
                if len(kde_y) > 1:
                    plot_dates = np.array(month_df["DATE"].dt.to_pydatetime())
                    
                    kde = stats.gaussian_kde(kde_y)
                    kde_x = np.linspace(kde_y.min() - std_y, kde_y.max() + std_y, 100)
                    kde_points = kde(kde_x)
                    
                    # Time Series Plot with Mean and Std Dev Lines
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
                    
                    # Histogram and KDE with Mean and Std Dev Lines
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
                                        
                    # Create summary table for each month
                    summary_table_data = [
                        ['Mean', f"{mean_y:.2f}"],
                        ['Median', f"{kde_y.median():.2f}"],
                        ['Std Dev', f"{std_y:.2f}"],
                        ['Min', f"{kde_y.min():.2f}"],
                        ['Max', f"{kde_y.max():.2f}"],
                        ['Missing Data (%)', f"{(kde_y.isna().sum() / len(kde_y)) * 100:.2f}%"],
                        ['Skewness', f"{kde_y.skew():.2f}"],
                        ['Kurtosis', f"{kde_y.kurtosis():.2f}"],
                    ]
                    fig.add_trace(
                        go.Table(
                            header=dict(
                                values=["Statistic", "Value"],
                                fill_color='black',
                                align='center',
                                font=dict(color='white', size=12),
                            ),
                            cells=dict(
                                values=[list(x) for x in zip(*summary_table_data)],
                                fill_color='white',
                                align='center',
                                font=dict(size=12),
                            )
                        ),
                        row=i, col=3
                    )
        
        fig.update_layout(
            title=dict(
                text=f"{metric} Analysis<br><sup>{title_info}</sup>",
                font=dict(size=22),
                y=0.98, 
                x=0.5
            ),
            height=1200,
            width=1600,
            template="plotly_white",
            showlegend=False,
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