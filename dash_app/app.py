
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dash import Dash, html, dcc
from dash.dependencies import Input, Output
from estimation_page.estimation_dashboard import estimation_layout

# Initialize the app
app = Dash(__name__, suppress_callback_exceptions=True, external_scripts=['https://cdn.plot.ly/plotly-latest.min.js'])
server = app.server

# Define the main layout with URL routing
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# Callback for page content based on URL
@app.callback(Output('page-content', 'children'), Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/estimation_page.estimation_dashboard':
        return estimation_layout
    else:
        return estimation_layout
    
# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)

