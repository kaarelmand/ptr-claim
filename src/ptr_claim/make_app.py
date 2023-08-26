from datetime import datetime, timezone

from dash import Dash, dcc, html, Input, Output

from .draw_map import draw_map


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
