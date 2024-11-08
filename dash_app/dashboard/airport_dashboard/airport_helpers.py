
import plotly.graph_objects as go
import pandas as pd
import plotly.figure_factory as ff
import plotly.express as px
from plotly.subplots import make_subplots

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

def create_time_series_chart(df, y_column, title):
    fig = px.line(
        df,
        x='FlightDate',
        y=y_column,
        title=title,
        markers=True,
        labels={y_column: title, 'FlightDate': 'Date'}
    )
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title=title,
        template="plotly_dark"
    )
    return fig

def create_cancellation_chart(df):
    cancellation_count = df.groupby('DayOfWeek')['Cancelled'].sum().reset_index()
    fig = px.bar(
        cancellation_count,
        x='DayOfWeek',
        y='Cancelled',
        title="Flight Cancellations by Day of the Week",
        labels={'DayOfWeek': 'Day of the Week', 'Cancelled': 'Number of Cancellations'}
    )
    return fig

def create_scatter_plot(df):
    fig = px.scatter(
        df,
        x='Distance',
        y='ActualElapsedTime',
        color='Marketing_Airline_Network',
        title="Distance vs Actual Elapsed Time",
        labels={'Distance': 'Distance (miles)', 'ActualElapsedTime': 'Elapsed Time (minutes)'}
    )
    return fig

def create_box_plot(df):
    fig = px.box(
        df,
        x='DayOfWeek',
        y='DepTime',
        title="Distribution of Departure Times by Day of the Week",
        labels={'DayOfWeek': 'Day of the Week', 'DepTime': 'Departure Time'}
    )
    return fig

def create_correlation_heatmap(df):
    correlation_matrix = df[['DepTime', 'ArrTime', 'CRSElapsedTime', 'ActualElapsedTime']].corr()
    fig = ff.create_annotated_heatmap(
        z=correlation_matrix.to_numpy(),
        x=correlation_matrix.columns.tolist(),
        y=correlation_matrix.columns.tolist(),
        colorscale='Viridis',
        showscale=True
    )
    fig.update_layout(title="Correlation Heatmap")
    return fig

def create_airport_dashboard(airport, airport_id, year, month):
    try:
        
        # Load data from Google Cloud Storage
        file_path = f"gs://airport-weather-data/transtat-bts/{airport}.csv"
        df = pd.read_csv(file_path, storage_options={"token": "flights-weather-project-f94d306bee1f.json"}, low_memory=False)
        df["FlightDate"] = pd.to_datetime(df["FlightDate"], errors='coerce')

        fig_height = 1200
        fig_width = 1600

        # Filter data for the specific month and year
        filtered_df = df[(df["FlightDate"].dt.month == month) & (df["FlightDate"].dt.year == year)].copy()

        if filtered_df.empty:
            raise ValueError(f"No data available for the selected month {month} and year {year} at airport {airport_id}.")

        # Create individual plotly figures
        time_series_fig = create_time_series_chart(filtered_df, 'ActualElapsedTime', f"Elapsed Time Over Time for {airport_id} in {year}-{month:02d}")
        cancellation_fig = create_cancellation_chart(filtered_df)
        scatter_fig = create_scatter_plot(filtered_df)
        box_plot_fig = create_box_plot(filtered_df)
        correlation_fig = create_correlation_heatmap(filtered_df)

        # Create subplots layout
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                "Time Series Chart",
                "Cancellations by Day of the Week",
                "Scatter Plot: Distance vs Elapsed Time",
                "Departure Times by Day of the Week",
                "Correlation Heatmap"
            ),
            specs=[[{"type": "xy"}, {"type": "bar"}],
                   [{"type": "scatter"}, {"type": "box"}],
                   [{"colspan": 2}, None]],
            vertical_spacing=0.15,
            horizontal_spacing=0.1
        )

        # Add traces from individual figures to the subplot
        for trace in time_series_fig.data:
            fig.add_trace(trace, row=1, col=1)
        for trace in cancellation_fig.data:
            fig.add_trace(trace, row=1, col=2)
        for trace in scatter_fig.data:
            fig.add_trace(trace, row=2, col=1)
        for trace in box_plot_fig.data:
            fig.add_trace(trace, row=2, col=2)
        for trace in correlation_fig.data:
            fig.add_trace(trace, row=3, col=1)

        # Update layout to accommodate subplots
        fig.update_layout(
            title=f"Airport Dashboard for {airport_id} in {year}-{month:02d}",
            height=fig_height,  
            width=fig_width,
            template="plotly_dark",
            showlegend=False
        )

        return fig

    except Exception as e:
        # Handle errors gracefully
        print(f"Error: {str(e)}")
        fig = create_default_plot()
        fig.add_annotation(
            text=f"Error loading data for airport {airport_id}:<br>{str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color="red")
        )
        fig.update_layout(
            title=f"Error - {airport_id} ({year}-{month})",
            template="plotly_dark",
            height=fig_height,  
            width=fig_width,
        )
        return fig
