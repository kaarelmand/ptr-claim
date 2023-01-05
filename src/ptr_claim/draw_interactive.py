from PIL import Image
import plotly.graph_objects as go
from plotly.colors import sample_colorscale

from ptr_claim.prep_data import _stages as stages


def draw_interactive(claims, map, corners, title, width=1000, cmap="RdYlGn"):

    fig = go.FigureWidget(
        layout_xaxis_range=(corners[0], corners[1]),
        layout_yaxis_range=(corners[2], corners[3]),
    )

    # Add background image
    fig.add_layout_image(
        dict(
            source=Image.open(map),
            x=corners[0],
            y=corners[3],
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
        fig.add_trace(
            go.Scatter(
                name=stage,
                x=data["cell_x_map"],
                y=data["cell_y_map"],
                # Plotly uses html tags, the 'details' column uses python escapes.
                text=data["details"].str.replace("\n", "<br>"),
                mode="markers",
                marker=dict(
                    size=data["count"],
                    sizemode="area",
                    # Recommended algo in plotly docs.
                    sizeref=2 * data["map_size"].max() / (40**2),
                    sizemin=4,
                    color=colordict[stage],
                    line=dict(width=1, color="DarkSlateGrey"),
                ),
            )
        )

    # Style image
    fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False)
    fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=False)
    aspect = (corners[1] - corners[0]) / (corners[3] - corners[2])
    fig.update_layout(
        title=title,
        legend={"itemsizing": "constant"},
        autosize=False,
        width=width,
        height=width / aspect,
    )
    return fig