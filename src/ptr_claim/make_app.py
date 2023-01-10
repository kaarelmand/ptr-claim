from datetime import datetime, timezone

from dash import Dash, dcc, html, Input, Output

from ptr_claim.draw_map import draw_map


def generate_row(ser):
    rowitems = [html.Td(val) for key, val in ser.iloc[:-1].items()]
    rowitems.append(html.Td(html.A(ser["url"], href=ser["url"])))
    return html.Tr(rowitems)


def generate_table(df):
    df = df[["title", "stage", "claimant", "reviewers", "url"]]
    output_cols = df.columns[:-1].str.capitalize().to_list() + ["Link"]
    tablehead = html.Thead(html.Tr([html.Th(col) for col in output_cols]))
    tablebody = html.Tbody([generate_row(row) for _, row in df.iterrows()])
    return html.Table([tablehead, tablebody])


def make_app(agg_claims, claims, mapfile, corners, width=900):

    fig = draw_map(
        claims=agg_claims,
        map=mapfile,
        corners=corners,
        width=width,
        title="",
    )

    app = Dash(
        __name__, external_stylesheets=["https://codepen.io/chriddyp/pen/bWLwgP.css"]
    )

    app.layout = html.Div(
        [
            html.H1(
                f"Tamriel Rebuilt | Interior claims",
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

    return app
