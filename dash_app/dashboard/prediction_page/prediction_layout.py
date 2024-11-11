
import pandas as pd
from dash import dcc, html

# Load options for prediction from the CSV
df_options = pd.read_csv("gs://airport-weather-data/options_for_prediction.csv", storage_options={"token": "flights-weather-project-f94d306bee1f.json"})

# Extract options for airlines and airports
airline_options = [{"label": airline, "value": airline} for airline in df_options['airline'].dropna().unique()]
airport_options = [
    {
        "label": f"{row['airport_display_name']} ({row['airport_code']}, ID: {row['airport_id']})",
        "value": row['airport_id']
    }
    for _, row in df_options.dropna(subset=['airport_id', 'airport_display_name', 'airport_code']).iterrows()
]

# Define layout for the prediction page
random_forest_prediction_layout = html.Div(
    className="prediction-container",
    children=[
        # Header
        html.H1(
            "Flight Delay & Cancellation Prediction",
            className="prediction-header",
            style={
                "textAlign": "center",
                "color": "white",  # Main title set to white
                "marginBottom": "50px",
                "fontSize": "3rem",
                "fontWeight": "bold",
            }
        ),
        
        # Main Input Sections
        html.Div(
            className="prediction-sections",
            style={
                "display": "grid",
                "gridTemplateColumns": "1fr 1fr 1fr",
                "gap": "20px",
                "maxWidth": "1600px",  # Widened container
                "margin": "0 auto",
                "padding": "20px"
            },
            children=[
                # Airline and Flight Date Section
                html.Div(
                    className="input-group",
                    children=[
                        html.Label("Airline", className="input-label", style={"fontWeight": "bold", "fontSize": "1.2rem", "color": "black", "marginBottom": "5px"}),
                        dcc.Dropdown(
                            id="airline-input",
                            options=airline_options,
                            placeholder="Select Airline",
                            className="dropdown",
                            style={"width": "100%", "fontSize": "1.1rem"},
                            searchable=True
                        ),
                        html.Div(id="airline-error", className="error-message", style={'color': 'red', "marginTop": "5px"}),
                        
                        html.Label("Flight Date", className="input-label", style={"fontWeight": "bold", "fontSize": "1.2rem", "color": "black", "marginTop": "20px", "marginBottom": "5px"}),
                        dcc.DatePickerSingle(
                            id="date-input",
                            placeholder="Select Date",
                            className="date-picker",
                            display_format="YYYY-MM-DD",
                            style={"width": "100%", "fontSize": "1.1rem"}
                        ),
                        html.Div(id="date-error", className="error-message", style={'color': 'red', "marginTop": "5px"})
                    ],
                    style={
                        "padding": "25px",
                        "border": "1px solid #e0e0e0",
                        "borderRadius": "8px",
                        "boxShadow": "0 4px 8px rgba(0,0,0,0.1)",
                        "backgroundColor": "#f9f9f9",
                        "width": "100%"
                    }
                ),
                
                # Origin Airport and Departure Time Section
                html.Div(
                    className="input-group",
                    children=[
                        html.Label("Origin Airport", className="input-label", style={"fontWeight": "bold", "fontSize": "1.2rem", "color": "black", "marginBottom": "5px"}),
                        dcc.Dropdown(
                            id="origin-airport-input",
                            options=airport_options,
                            placeholder="Select Origin Airport",
                            className="dropdown",
                            searchable=True,
                            style={"width": "100%", "fontSize": "1.1rem", "maxHeight": "1000px"}  # Increased dropdown height
                        ),
                        html.Div(id="origin-error", className="error-message", style={'color': 'red', "marginTop": "5px"}),

                        html.Label("Departure Time (Local - HH:MM)", className="input-label", style={"fontWeight": "bold", "fontSize": "1.2rem", "color": "black", "marginTop": "20px", "marginBottom": "5px"}),
                        dcc.Input(
                            id="departure-time-input",
                            type="text",
                            placeholder="Enter Departure Time (HH:MM)",
                            className="time-picker",
                            style={"width": "100%", "padding": "10px", "fontSize": "1.1rem"}
                        ),
                        html.Div(id="departure-time-error", className="error-message", style={'color': 'red', "marginTop": "5px"})
                    ],
                    style={
                        "padding": "25px",
                        "border": "1px solid #e0e0e0",
                        "borderRadius": "8px",
                        "boxShadow": "0 4px 8px rgba(0,0,0,0.1)",
                        "backgroundColor": "#f9f9f9",
                        "width": "100%"
                    }
                ),
                
                # Destination Airport and Arrival Time Section
                html.Div(
                    className="input-group",
                    children=[
                        html.Label("Destination Airport", className="input-label", style={"fontWeight": "bold", "fontSize": "1.2rem", "color": "black", "marginBottom": "5px"}),
                        dcc.Dropdown(
                            id="destination-airport-input",
                            options=airport_options,
                            placeholder="Select Destination Airport",
                            className="dropdown",
                            searchable=True,
                            style={"width": "100%", "fontSize": "1.1rem", "maxHeight": "500px"}  # Increased dropdown height
                        ),
                        html.Div(id="destination-error", className="error-message", style={'color': 'red', "marginTop": "5px"}),

                        html.Label("Arrival Time (Local - HH:MM)", className="input-label", style={"fontWeight": "bold", "fontSize": "1.2rem", "color": "black", "marginTop": "20px", "marginBottom": "5px"}),
                        dcc.Input(
                            id="arrival-time-input",
                            type="text",
                            placeholder="Enter Arrival Time (HH:MM)",
                            className="time-picker",
                            style={"width": "100%", "padding": "10px", "fontSize": "1.1rem"}
                        ),
                        html.Div(id="arrival-time-error", className="error-message", style={'color': 'red', "marginTop": "5px"})
                    ],
                    style={
                        "padding": "25px",
                        "border": "1px solid #e0e0e0",
                        "borderRadius": "8px",
                        "boxShadow": "0 4px 8px rgba(0,0,0,0.1)",
                        "backgroundColor": "#f9f9f9",
                        "width": "100%"
                    }
                )
            ]
        ),
        
        # Predict Button and Output Section
        html.Div(
            html.Button(
                "Predict Delays and Cancellation",
                id="predict-button",
                className="predict-button",
                n_clicks=0,
                style={
                    "backgroundColor": "#5c6bc0",
                    "color": "white",
                    "fontWeight": "bold",
                    "border": "none",
                    "padding": "15px 30px",
                    "fontSize": "1.2rem",
                    "cursor": "pointer",
                    "marginTop": "40px",
                    "borderRadius": "8px",
                    "boxShadow": "0 4px 8px rgba(0,0,0,0.2)"
                }
            ),
            style={"textAlign": "center"}
        ),
        
        # Loading Spinner and Prediction Output
        dcc.Loading(
            id="loading-prediction",
            type="circle",
            children=html.Div(id="prediction-output", style={'padding': '30px', 'color': '#2b3e50', "fontSize": "1.3rem", "textAlign": "center"}),
            style={
                'marginTop': '50px',
                'fontSize': '1.3rem'
            }
        )
    ]
)
