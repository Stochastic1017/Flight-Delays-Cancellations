
import plotly.express as px

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
