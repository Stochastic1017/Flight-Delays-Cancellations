
from dash import html, dcc
from .weather_dashboard.weather_layout import weather_dashboard_layout
from .airport_dashboard.airport_layout import airport_dashboard_layout
import dashboard.weather_dashboard.weather_callback
import dashboard.airport_dashboard.airport_callback

# Main layout that aggregates different dashboards
main_dashboard_layout = html.Div([
    dcc.Tabs(id="tabs-dashboard", value='weather-dashboard', children=[
        dcc.Tab(label='Explore Weather Data', value='weather-dashboard', children=[weather_dashboard_layout]),
        dcc.Tab(label='Explore Airport Data', value='airport-dashboard', children=[airport_dashboard_layout]),
    ]),
])
