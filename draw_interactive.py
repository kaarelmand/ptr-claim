import argparse
import pandas as pd
from PIL import Image
from datetime import date
import plotly.graph_objects as go
from plotly.colors import sample_colorscale

from prep_data import _stages as stages
from prep_data import CELL_SIZE as cell_size


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


def main():
    parser = argparse.ArgumentParser(
        prog="",
        description="Draws an interactive image of Tamriel Rebuilt claims.",
    )
    parser.add_argument(
        "-i",
        "--input",
        default="aggregated_claims.json",
        help=(
            "Json file containing per-cell aggregated claims. Defaults to "
            + "'aggregated_claims.json'."
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        default="TR_int_claims.html",
        help="Output image file. Defaults to 'TR_int_claims.html'.",
    )
    parser.add_argument(
        "-m",
        "--map",
        default="Tamriel Rebuilt Province Map_2022-11-25.png",
        help=(
            "Map file on which to draw the claims. Defaults to 'Tamriel Rebuilt "
            + "Province Map_2022-11-25.png'."
        ),
    )
    parser.add_argument(
        "-w", "--width", default=1000, help="Output image width (px). Defaults to 1000."
    )
    parser.add_argument(
        "-c",
        "--corners",
        default="-42 61 -64 38",
        help=(
            "Cell coordinates for the corners of the provided map. Four integers "
            + "separated by spaces. Defaults to '-42 61 -64 38'."
        ),
    )
    parser.add_argument(
        "-t",
        "--title",
        default=f"Tamriel Rebuilt interior claims {date.today()}",
        help=(
            "Title to be printed on the output. Defaults to 'Tamriel Rebuilt "
            + "interior claims {date.today()}'."
        ),
    )
    args = parser.parse_args()

    claims = pd.read_json(args.input)
    gridmap_corners = [int(c) * cell_size for c in args.corners.split()]
    fig = draw_interactive(
        claims=claims,
        map=args.map,
        corners=gridmap_corners,
        title=args.title,
        width=args.width,
    )

    fig.write_html(args.output)


if __name__ == "__main__":
    main()
