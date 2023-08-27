from PIL import Image
import plotly.graph_objects as go
from plotly.colors import sample_colorscale

from .prep_data import _stages as stages


def draw_map(claims, map, corners, title, width=1000, cmap="Plasma"):
    fig = go.FigureWidget(
        layout_xaxis_range=(corners[0], corners[1]),
        layout_yaxis_range=(corners[2], corners[3]),
    )

    # Add background image
    fig.add_layout_image(
        dict(
            source=Image.open(map),
            x=corners[0] - 0.5,
            y=corners[3] - 0.5,
            xref="x",
            yref="y",
            sizex=corners[1] - corners[0],
            sizey=corners[3] - corners[2],
            sizing="stretch",
            opacity=0.5,
            layer="below",
        )
    )

    # Set up colors
    presentstages = [
        stage for stage in stages if stage in claims["stage_mean"].to_list()
    ]
    colors = sample_colorscale(cmap, len(presentstages))
    colordict = dict(zip(presentstages, colors))

    # Draw claims
    for stage in presentstages:
        data = claims[claims["stage_mean"] == stage]
        if stage == "Design":
            visible = "legendonly"
        else:
            visible = True
        x = data["cell_x"]
        y = data["cell_y"]
        fig.add_trace(
            go.Scatter(
                name=stage,
                x=x,
                y=y,
                # Plotly uses html tags, the 'details' column uses Python escapes.
                text=data["details"].str.replace("\n", "<br>"),
                customdata=data[["cell_x", "cell_y"]],
                hovertemplate="<b>Cell: %{x:d}, %{y:d}</b><br>%{text}"
                + "<extra></extra>",
                mode="markers",
                marker=dict(
                    size=data["count"],
                    sizemode="area",
                    # Recommended algorithm in Plotly docs.
                    sizeref=2 * data["map_size"].max() / (40**2),
                    sizemin=4,
                    color=colordict[stage],
                    line=dict(width=1, color="DarkSlateGrey"),
                ),
                visible=visible,
            )
        )

    # Style image
    fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False)
    fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=False)
    aspect = (corners[1] - corners[0]) / (corners[3] - corners[2])
    fig.update_layout(
        # The anchor fixes the aspect ratio.
        yaxis_scaleanchor="x",
        title=title,
        legend={"itemsizing": "constant"},
        autosize=False,
        margin=dict(l=10, r=10, t=20, b=10),
        width=width,
        # The magic number 135 is there because I can't figure out how to calculate the
        # space taken up by the legend.
        height=width / aspect - 135,
    )
    return fig
