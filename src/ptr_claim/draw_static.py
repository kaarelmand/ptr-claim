import argparse
from cycler import cycler
from datetime import date

import matplotlib.pyplot as plt
from matplotlib import lines as mlines
import numpy as np
import pandas as pd

from prep_data import _stages as stages
from prep_data import CELL_SIZE as cell_size


def draw_by_stage(ax, claims):
    # Remove merged claims from the list.
    less_stages = [stage for stage in stages if stage in claims["stage_mean"].to_list()]
    # List of colors corresponding to the stages.
    cmap = plt.cm.get_cmap("RdYlGn")
    colors = [cmap(i) for i in np.linspace(0, 1, len(less_stages))]
    ax.set_prop_cycle(cycler(color=colors))

    # Draw claims
    for stage in less_stages:
        ax.scatter(
            data=claims[claims["stage_mean"] == stage],
            x="cell_x_map",
            y="cell_y_map",
            s="map_size",
            edgecolor="black",
            linewidth=0.5,
            label=stage,
        )

    # Custom legend
    stage_handles = [
        mlines.Line2D(
            [],
            [],
            linewidth=0,
            marker="o",
            c=color,
            markersize=np.sqrt(30),
            markeredgewidth=0.5,
            markeredgecolor="black",
        )
        for color in colors
    ]
    stage_leg = ax.legend(
        handles=stage_handles, labels=less_stages, loc="upper right", title="Stage"
    )


def make_count_legend(ax, labels, **kwargs):
    if not kwargs:
        kwargs = dict(
            linewidth=0,
            marker="o",
            c="white",
            markeredgewidth=0.5,
            markeredgecolor="black",
        )
    count_handles = [
        mlines.Line2D([], [], markersize=np.sqrt((np.log(s) + 1) * 30), **kwargs)
        for s in labels
    ]
    count_leg = ax.legend(
        handles=count_handles,
        labels=labels,
        loc="upper right",
        bbox_to_anchor=(0.85, 1),
        title="Claims count",
    )
    return count_leg


def draw_claim_fig(
    claims,
    map,
    corners=(-42, 61, -64, 38),
    width=15,
    count_labels=(1, 2, 5, 10, 20, 50),
    title=f"Tamriel Rebuilt interior claims {date.today()}",
):
    aspect = (corners[1] - corners[0]) / (corners[3] - corners[2])
    fig, ax = plt.subplots(figsize=(width, width / aspect))

    mapfile = plt.imread(map)
    ax.imshow(mapfile, extent=[n * cell_size for n in corners], alpha=0.5)

    count_leg = make_count_legend(ax, count_labels)
    draw_by_stage(ax, claims)

    ax.add_artist(count_leg)

    # Map title
    ax.text(
        x=0.01,
        y=0.99,
        s=title,
        va="top",
        transform=ax.transAxes,
        fontsize="x-large",
        fontweight="bold",
    )
    ax.axis("off")
    return fig, ax


def main():
    parser = argparse.ArgumentParser(
        prog="",
        description="Draws a static image of Tamriel Rebuilt claims.",
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
        default="TR_int_claims.png",
        help="Output image file. Defaults to 'TR_int_claims.png'.",
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
        "-w", "--width", default=15, help="Output image width (in). Defaults to 15."
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
    gridmap_corners = [int(c) for c in args.corners.split()]

    fig, ax = draw_claim_fig(
        claims=claims,
        map=args.map,
        corners=gridmap_corners,
        width=args.width,
        title=args.title,
    )
    fig.savefig(args.output, bbox_inches="tight")


if __name__ == "__main__":
    main()
