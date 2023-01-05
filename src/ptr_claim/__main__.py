import argparse
from datetime import date
import os

import pandas as pd

from ptr_claim.draw_interactive import draw_interactive
from ptr_claim.prep_data import CELL_SIZE as cell_size
from ptr_claim.prep_data import prep_data
from ptr_claim.scrape_tr import crawl


def visualize_ptr_claims(
    starturl,
    scrape_outfile,
    gridmap_corners,
    mapfile,
    title=f"Tamriel Rebuilt interior claims {date.today()}",
    width=1000,
    methods="itue",
):
    # Crawl the website.
    # TO DO -- make crawl output a python object, not a json file. Related to
    #   scrapy Items.
    crawl(starturl, scrape_outfile)

    # Prepare the data.
    claims = pd.read_json(scrape_outfile)
    agg_claims = prep_data(claims=claims, methods=methods)

    # Draw figure.
    fig = draw_interactive(
        claims=agg_claims,
        map=mapfile,
        corners=gridmap_corners,
        title=title,
        width=width,
    )
    return fig


def main():
    parser = argparse.ArgumentParser(
        prog="ptr-claim",
        description="Visualize interior claims on the Tamriel Rebuilt claims browser.",
    )
    parser.add_argument(
        "-u",
        "--url",
        default="https://www.tamriel-rebuilt.org/claims/interiors",
        help=(
            "Claims browser page containing claims to be scraped. Defaults to "
            + "'https://www.tamriel-rebuilt.org/claims/interiors'."
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        default="TR_int_claims.html",
        help="Output interactive image file. Defaults to 'TR_int_claims.html'.",
    )
    parser.add_argument(
        "-s",
        "--scrapefile",
        default="interiors.json",
        help="JSON file to store scraping outputs in. Defaults to 'interiors.json'",
    )
    parser.add_argument(
        "-w", "--width", default=1000, help="Output image width (px). Defaults to 1000."
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
    parser.add_argument(
        "-M",
        "--methods",
        default="itue",
        help=(
            """How to locate missing claim coordinates.
                'i' uses optical character recognition on claim images.
                't' uses parts of the title to guess the coordinates.
                'u' uses known URLs. 
                'e' fixes Embers of Empire coordinates.
            You can specify several flags.
            Defaults to "itue".
        """
        ),
    )

    args = parser.parse_args()

    # TO DO: make background map configurable
    mapfile = os.path.join(
        os.path.dirname(__file__), "data", "Tamriel Rebuilt Province Map_2022-11-25.png"
    )
    gridmap_corners = "-42 61 -64 38"
    gridmap_corners = [int(c) * cell_size for c in gridmap_corners.split()]

    fig = visualize_ptr_claims(
        starturl=args.url,
        scrape_outfile=args.output,
        gridmap_corners=gridmap_corners,
        mapfile=mapfile,
        title=args.title,
        width=args.width,
        methods=args.methods,
    )

    fig.write_html(args.output)
    print(f"Finished. Claim map saved to {args.output}.")


if __name__ == "__main__":
    main()
