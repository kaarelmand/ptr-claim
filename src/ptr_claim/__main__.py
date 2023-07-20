from datetime import datetime, timezone
import os

import pandas as pd
from dash import Dash, html, dcc, Output, Input

from ptr_claim.draw_map import draw_map
from ptr_claim.prep_data import prep_data
from ptr_claim.scrape_tr import crawl
from ptr_claim.make_app import generate_table


SCRAPESWITCH = os.environ.get("PTR_SCRAPESWITCH", "True")
URL = os.environ.get("PTR_URL", "https://www.tamriel-rebuilt.org/claims/interiors")
SCRAPEFILE = os.environ.get("PTR_SCRAPEFILE", "interiors.json")
METHODS = os.environ.get("PTR_METHODS", "itue")
MAPFILE = os.environ.get("PTR_MAPFILE", "Tamriel_Rebuilt_Claims_Map_2023-07-13.png")
MAPCORNERS = os.environ.get("PTR_MAPCORNERS", "-42 61 -64 38")
WIDTH = os.environ.get("PTR_WIDTH", "900")


if SCRAPESWITCH.lower().strip() in ("true", "t", "yes", "y", "1"):
    crawl(URL, SCRAPEFILE)

try:
    claims = pd.read_json(SCRAPEFILE)
except ValueError as err:
    raise Exception(f"Cannot read {SCRAPEFILE}. Is it a valid .json file?")

agg_claims = prep_data(claims=claims, methods=METHODS)

# TODO: figure out how to use importlib.resources here, or at least Pathlib
mapfile = os.path.join(os.path.dirname(__file__), "data", MAPFILE)
gridmap_corners = [int(c) for c in MAPCORNERS.split()]

fig = draw_map(
    claims=agg_claims,
    map=mapfile,
    corners=gridmap_corners,
    width=float(WIDTH),
    title="",
)

app = Dash(
    __name__, external_stylesheets=["https://codepen.io/chriddyp/pen/bWLwgP.css"]
)
# Entry point for gunicorn.
server = app.server

app.layout = html.Div(
    [
        html.H1(
            "Tamriel Rebuilt | Interior claims",
        ),
        html.Div(datetime.now(timezone.utc).strftime(r"%Y-%m-%d %H:%M %Z")),
        dcc.Graph(id="clickable-graph", figure=fig),
        html.Div(
            id="claim-info-output",
        ),
    ],
)


@app.callback(
    Output("claim-info-output", "children"), Input("clickable-graph", "clickData")
)
def display_on_click(clickData):
    try:
        x, y = clickData["points"][0]["customdata"]
        filtered_data = claims[(claims["cell_x"] == x) & (claims["cell_y"] == y)]
        return generate_table(filtered_data)
    except TypeError:
        return "Click on any point to show claim information."


def main():
    app.run_server(debug=True)


if __name__ == "__main__":
    main()
