
import gcsfs
import plotly.graph_objects as go
import pandas as pd
import plotly.figure_factory as ff
import plotly.express as px
from plotly.subplots import make_subplots

# Initialize Google Cloud Storage FileSystem
fs = gcsfs.GCSFileSystem(project='Flights-Weather-Project', token='flights-weather-project-f94d306bee1f.json')

# Initial Plot Message
def create_default_plot():
    fig = go.Figure()
    fig.update_layout(
        plot_bgcolor="black",
        paper_bgcolor="black",
        title="Station Time-Series Overview",
        height=600,
        width=800,
        template="plotly_dark"
    )
    return fig

def create_airport_map_figure(mapbox_style, marker_size, marker_opacity, filtered_df, color_scale, color_by_metric=''):
    # Verify if the selected color metric exists in the dataframe
    color_column = color_by_metric if color_by_metric and color_by_metric in filtered_df.columns else None

    hover_data = {
        "DISPLAY_AIRPORT_CITY_NAME_FULL": True,
        "AIRPORT": True,
        "State": True,
        "City": True,
        color_column: True if color_column else False
    }

    # Create the map figure with color gradient if color_column is valid
    fig = px.scatter_mapbox(
        filtered_df,
        lat="LATITUDE",
        lon="LONGITUDE",
        hover_name="AIRPORT_ID",
        hover_data=hover_data,
        color=color_column,  # Apply color gradient if a valid metric is selected
        color_continuous_scale=color_scale if color_column else None
    ).update_traces(marker=dict(size=marker_size, opacity=marker_opacity))

    # Update layout
    fig.update_layout(
        mapbox=dict(
            style=f"mapbox://styles/mapbox/{mapbox_style}",
            zoom=3.5,
            center={"lat": 37.0902, "lon": -95.7129},
        ),
        coloraxis_colorbar=dict(
            title=color_by_metric.replace("Avg", "Average ").replace("CancellationRate", "Cancellation Rate"),
            ticksuffix="%" if color_by_metric == "CancellationRate" else " min",
        ) if color_column else None,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        showlegend=False
    )
    return fig

def create_delay_plots(airport_id, year, month, title_info):
    try:
        file_path = f"gs://airport-weather-data/merged_data/{airport_id}_training_data.csv"
        df = pd.read_csv(
            file_path,
            storage_options={"token": "flights-weather-project-f94d306bee1f.json"},
            low_memory=False,
        )
        df["UTC_DATE"] = pd.to_datetime(df["UTC_DATE"], errors="coerce")

        # Filter data for the selected year and month
        df = df[(df["UTC_DATE"].dt.year == year) & (df["UTC_DATE"].dt.month == month)]

        if df.empty:
            # Display message if there's no data
            fig = go.Figure()
            fig.add_annotation(
                text=f"No data available for airport {airport_id}, year {year}, month {month}",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=24, color="red"),
            )
            fig.update_layout(
                title=f"Data Unavailable - {airport_id} ({year}-{month})",
                template="plotly_dark",
                height=1060,
                width=1510,
            )
            return fig

        # Load airport metadata for name lookup
        airport_metadata = f"gs://airport-weather-data/airports-list-us.csv"
        df_airport = pd.read_csv(
            airport_metadata,
            storage_options={"token": "flights-weather-project-f94d306bee1f.json"},
        )

        # Merge to get destination airport names
        df = df.merge(
            df_airport[["AIRPORT_ID", "DISPLAY_AIRPORT_NAME"]],
            left_on="DestAirportID",
            right_on="AIRPORT_ID",
            how="left",
        )

        # Map day of the week to names
        day_map = {1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat", 7: "Sun"}
        df["DayOfWeek"] = df["DayOfWeek"].map(day_map)

        # Prepare data for each delay type
        delay_types = [
            {"column": "ArrivalDelay", "label": "Arrival Delay", "color": "#1f77b4"},
            {"column": "DepartureDelay", "label": "Departure Delay", "color": "#ff7f0e"},
            {"column": "TotalFlightDelay", "label": "Total Flight Delay", "color": "#2ca02c"},
            {"column": "TaxiDelay", "label": "Taxi Delay", "color": "#d62728"},
        ]

        # Create the subplot structure with 4 fixed columns for each delay type
        fig = make_subplots(
            rows=4,
            cols=4,
            subplot_titles=[
                f"{dt['label']} Distribution" for dt in delay_types
            ]
            + [f"{dt['label']} by Day of Week" for dt in delay_types]
            + [f"{dt['label']} by Marketing Airline" for dt in delay_types]
            + [f"{dt['label']} by Destination Airport" for dt in delay_types],
            vertical_spacing=0.08,
            horizontal_spacing=0.03,
        )

        for idx, dt in enumerate(delay_types):
            col = idx + 1
            delay = dt["column"]
            label = dt["label"]
            color = dt["color"]

            # Row 1: Distribution
            fig.add_trace(
                go.Histogram(
                    x=df[delay].dropna(),
                    histnorm="probability density",
                    marker=dict(color=color),
                    name=label,
                    showlegend=False,
                ),
                row=1,
                col=col,
            )

            # Row 2: Box plot by Day of Week (outliers hidden)
            fig.add_trace(
                go.Box(
                    y=df[delay].dropna(),
                    x=df["DayOfWeek"],
                    marker=dict(color=color),
                    name=label,
                    boxpoints=False,  # Hide outliers
                    showlegend=False,
                ),
                row=2,
                col=col,
            )

            # Row 3: Box plot by Marketing Airline (outliers hidden)
            fig.add_trace(
                go.Box(
                    y=df[delay].dropna(),
                    x=df["Marketing_Airline_Network"],
                    marker=dict(color=color),
                    name=label,
                    boxpoints=False,  # Hide outliers
                    showlegend=False,
                ),
                row=3,
                col=col,
            )

            # Row 4: Box plot by Destination Airport (outliers hidden)
            fig.add_trace(
                go.Box(
                    y=df[delay].dropna(),
                    x=df["DISPLAY_AIRPORT_NAME"],
                    marker=dict(color=color),
                    name=label,
                    boxpoints=False,  # Hide outliers
                    showlegend=False,
                ),
                row=4,
                col=col,
            )

        fig.update_layout(
            title=dict(
                text=f"{title_info} - Delay Analysis",
                font=dict(size=22),
                y=0.98,
                x=0.5,
            ),
            height=1060,
            width=1510,
            template="plotly_dark",
            hovermode="closest",
            margin=dict(t=100, b=50, l=50, r=50),
            showlegend=False,
        )

        return fig

    except Exception as e:
        print(f"Error: {str(e)}")
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error loading data for airport {airport_id}:<br>{str(e)}",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=14, color="red"),
        )
        fig.update_layout(
            title=f"Error - {airport_id} ({year}-{month})",
            template="plotly_dark",
            height=1060,
            width=1510,
        )
        return fig
    
def create_cancellation_plot(airport_id, year, month, title_info):
    try:
        # Load the main dataset
        file_path = f"gs://airport-weather-data/merged_data/{airport_id}_training_data.csv"
        df = pd.read_csv(file_path, storage_options={"token": "flights-weather-project-f94d306bee1f.json"}, low_memory=False)
        df["UTC_DATE"] = pd.to_datetime(df["UTC_DATE"], errors='coerce')
        
        # Load airport metadata for name lookup
        airport_metadata = f"gs://airport-weather-data/airports-list-us.csv"
        df_airport = pd.read_csv(airport_metadata, storage_options={"token": "flights-weather-project-f94d306bee1f.json"})
        
        # Filter data for the selected year and month
        df = df[(df["UTC_DATE"].dt.year == year) & (df["UTC_DATE"].dt.month == month)]
        
        if df.empty:
            # Display message if there's no data
            fig = go.Figure()
            fig.add_annotation(
                text=f"No data available for airport {airport_id}, year {year}, month {month}",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=24, color="red")
            )
            fig.update_layout(
                title=f"Data Unavailable - {airport_id} ({year}-{month})",
                template='plotly_dark',
                height=1060,
                width=1510
            )
            return fig
        
        # Merge to get destination airport names
        df = df.merge(df_airport[['AIRPORT_ID', 'DISPLAY_AIRPORT_NAME']], left_on='DestAirportID', right_on='AIRPORT_ID', how='left')
        
        fig_height = 1060
        fig_width = 1510
        plot_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']  # Colors for each distinct plot

        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[
                "Cancelled vs Not Cancelled Flights",
                "Cancellations by Day of the Week",
                "Cancellations by Marketing Airline",
                "Cancellations by Destination Airport"
            ]
        )
        
        # 1. Bar chart of cancelled vs not cancelled flights
        cancel_counts = df['Cancelled'].value_counts()
        fig.add_trace(
            go.Bar(
                x=['Not Cancelled', 'Cancelled'],
                y=[cancel_counts.get(0, 0), cancel_counts.get(1, 0)],
                marker=dict(color=plot_colors[0]),
            ),
            row=1, col=1
        )

        # 2. Cancellations by day of the week
        day_of_week_cancel = df[df['Cancelled'] == 1]['DayOfWeek'].value_counts().sort_index()
        fig.add_trace(
            go.Bar(
                x=day_of_week_cancel.index,
                y=day_of_week_cancel.values,
                marker=dict(color=plot_colors[1]),
            ),
            row=1, col=2
        )

        # 3. Cancellations by marketing airline
        airline_cancel = df[df['Cancelled'] == 1]['Marketing_Airline_Network'].value_counts()
        fig.add_trace(
            go.Bar(
                x=airline_cancel.index,
                y=airline_cancel.values,
                marker=dict(color=plot_colors[2]),
            ),
            row=2, col=1
        )

        # 4. Cancellations by destination airport
        destination_cancel = df[df['Cancelled'] == 1]['DISPLAY_AIRPORT_NAME'].value_counts()
        fig.add_trace(
            go.Bar(
                x=destination_cancel.index,
                y=destination_cancel.values,
                marker=dict(color=plot_colors[3]),
            ),
            row=2, col=2
        )

        fig.update_layout(
            title=dict(
                text=f"{title_info} - Flight Cancellation Analysis",
                font=dict(size=22),
                y=0.98,
                x=0.5
            ),
            height=fig_height,
            width=fig_width,
            template="plotly_dark",
            showlegend=False,
            hovermode='closest',
            margin=dict(t=100, b=50, l=50, r=50)
        )
        
        return fig

    except Exception as e:
        print(f"Error: {str(e)}")
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error loading data for airport {airport_id}:<br>{str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color="red")
        )
        fig.update_layout(
            title=f"Error - {airport_id} ({year}-{month})",
            template='plotly_dark',
            height=1060,
            width=1510
        )
        return fig
    