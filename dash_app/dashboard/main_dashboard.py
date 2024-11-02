
from dash import html
from .weather_dashboard.weather_layout import weather_dashboard_layout
import dashboard.weather_dashboard.weather_callback  # Register callbacks

# Main layout that aggregates different dashboards
main_dashboard_layout = html.Div([
    html.H1("Multi-Dashboard Application"),
    weather_dashboard_layout  # Add more layouts like airport_dashboard_layout when available
])
