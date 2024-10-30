
import pandas as pd
import plotly.express as px
from dash import dcc, html, callback, Output, Input

# Mapbox token (hidden)
mapbox_token = "pk.eyJ1Ijoic3RvY2hhc3RpYzEwMTciLCJhIjoiY20ydmJpMzhrMGIwdDJqb2NoZGt5emw0YiJ9.QJXmXS_gHKVxDV4mVkmIOw"
px.set_mapbox_access_token(mapbox_token)

# Load data (keeping your existing data loading code)
df_station = pd.read_csv("https://raw.githubusercontent.com/Stochastic1017/Flight-Delays-Cancellations/refs/heads/main/stats/metadata/ncei-lcd-list-us.csv")
df_airport = pd.read_csv("https://raw.githubusercontent.com/Stochastic1017/Flight-Delays-Cancellations/refs/heads/main/stats/metadata/airports-list-us.csv")

# List of states for dropdown
states = sorted(df_airport['AIRPORT_STATE_CODE'].dropna().unique())

# Color scales
weather_color_scale = px.colors.cyclical.IceFire

# Layout with improved styling and inline CSS
estimation_layout = html.Div([
    html.H1("Enhanced US Map: Weather Stations & Airports", 
            style={
                'text-align': 'center', 
                'color': '#333',
                'margin': '20px 0',
                'font-family': 'Arial, sans-serif'
            }),
    
    # Control panel
    html.Div([
        html.Div([
            html.Label('Select Data Type', style={
                'font-weight': 'bold',
                'margin-bottom': '8px',
                'display': 'block'
            }),
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
            html.Label('Map Style', style={
                'font-weight': 'bold',
                'margin-bottom': '8px',
                'display': 'block'
            }),
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
            html.Label('Marker Size', style={
                'font-weight': 'bold',
                'margin-bottom': '8px',
                'display': 'block'
            }),
            dcc.Slider(
                id='marker-size',
                min=5,
                max=25,
                step=1,
                value=15,
                marks={i: str(i) for i in range(5, 26, 5)},
                className='custom-slider'
            )
        ], style={'margin-bottom': '25px'}),
        
        html.Div([
            html.Label('Marker Opacity', style={
                'font-weight': 'bold',
                'margin-bottom': '8px',
                'display': 'block'
            }),
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
        'width': '320px',
        'float': 'left',
        'padding': '30px',
        'background': '#f8f9fa',
        'border-radius': '10px',
        'box-shadow': '0 2px 4px rgba(0,0,0,0.1)',
        'margin': '20px',
        'font-family': 'Arial, sans-serif'
    }),
    
    # Map display
    html.Div([
        dcc.Graph(
            id="enhanced-map",
            config={"scrollZoom": True},
            style={'width': 'calc(100% - 360px)', 'height': '80vh'}
        )
    ], style={'margin-left': '360px', 'padding': '20px'}),
    
])

@callback(
    Output("enhanced-map", "figure"),
    [Input("data-selector", "value"),
     Input("mapbox-style-selector", "value"),
     Input("marker-size", "value"),
     Input("marker-opacity", "value")]
)
def update_enhanced_map(selected_data, mapbox_style, marker_size, marker_opacity):
    
    if selected_data == 'stations':
        fig = create_enhanced_weather_map(
            df_station,
            marker_size=marker_size,
            marker_opacity=marker_opacity
        )
        
    else:
        fig = create_enhanced_airport_map(
            df_airport,
            marker_size=marker_size,
            marker_opacity=marker_opacity
        )
    
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

def create_enhanced_weather_map(df, marker_size=15, marker_opacity=0.7):
    return px.scatter_mapbox(
        df,
        lat="latitude",
        lon="longitude",
        hover_name="station_name",
        hover_data={
            "station_name": True,
            "elevation": True,
            "admin1": True,
            "admin2": True
        },
        color="elevation",
        color_continuous_scale=weather_color_scale,
        range_color=[df['elevation'].min(), df['elevation'].max()],
    ).update_traces(
        marker=dict(
            size=marker_size,
            opacity=marker_opacity,
        )
    )

def create_enhanced_airport_map(df, marker_size=15, marker_opacity=0.7):
    return px.scatter_mapbox(
        df,
        lat="LATITUDE",
        lon="LONGITUDE",
        hover_name="AIRPORT",
        hover_data={
            "DISPLAY_AIRPORT_NAME": True,
            "City": True,
            "AIRPORT_STATE_NAME": True
        },
        color="AIRPORT_STATE_CODE",
    ).update_traces(
        marker=dict(
            size=marker_size,
            opacity=marker_opacity,
        )
    )
