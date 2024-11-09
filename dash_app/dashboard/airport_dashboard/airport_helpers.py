
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

def create_airport_map_figure(mapbox_style, marker_size, marker_opacity, filtered_df):
    fig = px.scatter_mapbox(
        filtered_df,
        lat="LATITUDE",
        lon="LONGITUDE",
        hover_name="AIRPORT_ID",
        hover_data={"DISPLAY_AIRPORT_CITY_NAME_FULL": True, 
                    "AIRPORT": True, 
                    "State": True, 
                    "City": True},
    ).update_traces(marker=dict(size=marker_size, opacity=marker_opacity))
    fig.update_layout(
        mapbox=dict(
            style=f"mapbox://styles/mapbox/{mapbox_style}",
            zoom=3.5,
            center={"lat": 37.0902, "lon": -95.7129},
        ),
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        showlegend=False
    )
    return fig

def create_delay_plots(airport_id, year, title_info):
    try:
        file_path = f"gs://airport-weather-data/merged_data/{airport_id}_training_data.csv"
        df = pd.read_csv(file_path, storage_options={"token": "flights-weather-project-f94d306bee1f.json"}, low_memory=False)
        df["UTC_DATE"] = pd.to_datetime(df["UTC_DATE"], errors='coerce')
        
        # Filter data for the selected year
        df = df[df["UTC_DATE"].dt.year == year]
        
        if df.empty:
            raise ValueError(f"No data available for airport: {airport_id}, {year}")
        
        fig_height = 1800
        fig_width = 1600
        colors = ['#00B4D8', '#4C9A2A']  # Colors for arrival and departure plots

        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=[
                "Arrival Delay Distribution", "Departure Delay Distribution",
                "Box Plot of Arrival Delay by Day of Week", "Box Plot of Departure Delay by Day of Week",
                "Scatter Plot: Arrival vs Departure Delay", "Correlation Plot: Arrival vs Departure Delay"
            ],
            specs=[[{"type": "xy"}, {"type": "xy"}],
                   [{"type": "box"}, {"type": "box"}],
                   [{"type": "scatter"}, {"type": "xy"}]]
        )
        
        # 1. Histogram of Arrival Delay
        fig.add_trace(
            go.Histogram(
                x=df['ArrivalDelay'].dropna(),
                histnorm='probability density',
                marker=dict(color=colors[0], opacity=0.7),
                nbinsx=30
            ),
            row=1, col=1
        )

        # 2. Histogram of Departure Delay
        fig.add_trace(
            go.Histogram(
                x=df['DepartureDelay'].dropna(),
                histnorm='probability density',
                marker=dict(color=colors[1], opacity=0.7),
                nbinsx=30
            ),
            row=1, col=2
        )

        # 3. Box Plot of Arrival Delay by Day of the Week
        fig.add_trace(
            go.Box(
                y=df['ArrivalDelay'].dropna(),
                x=df['DayOfWeek'],
                marker=dict(color=colors[0]),
            ),
            row=2, col=1
        )

        # 4. Box Plot of Departure Delay by Day of the Week
        fig.add_trace(
            go.Box(
                y=df['DepartureDelay'].dropna(),
                x=df['DayOfWeek'],
                marker=dict(color=colors[1]),
            ),
            row=2, col=2
        )

        # 5. Scatter Plot of Arrival Delay vs Departure Delay
        fig.add_trace(
            go.Scatter(
                x=df['ArrivalDelay'],
                y=df['DepartureDelay'],
                mode='markers',
                marker=dict(color='purple', opacity=0.5),
            ),
            row=3, col=1
        )

        # 6. Correlation Plot: Arrival vs Departure Delay
        corr_matrix = df[['ArrivalDelay', 'DepartureDelay']].corr().values
        fig.add_trace(
            go.Heatmap(
                z=corr_matrix,
                x=['ArrivalDelay', 'DepartureDelay'],
                y=['ArrivalDelay', 'DepartureDelay'],
                colorscale='Viridis',
                colorbar=dict(title="Correlation Coefficient")
            ),
            row=3, col=2
        )

        fig.update_layout(
            title=dict(
                text=f"{title_info} - Arrival vs Departure Delay Analysis",
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
            title=f"Error - {airport_id} ({year})",
            template='plotly_dark',
            height=fig_height,
            width=fig_width
        )
        return fig

    