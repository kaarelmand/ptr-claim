import argparse
from datetime import date
import logging
import os
from threading import Timer
import webbrowser

import pandas as pd

from ptr_claim.draw_map import draw_map
from ptr_claim.prep_data import prep_data
from ptr_claim.scrape_tr import crawl
from ptr_claim.make_app import make_app


def static_output(args, gridmap_corners, mapfile):
    # Crawl the website.
    # TO DO -- make crawl output a python object, not a json file. Related to scrapy
    #   Items.
    if not args.noscrape:
        crawl(args.url, args.scrapefile)

    # Prepare the data.
    claims = pd.read_json(args.scrapefile)
    agg_claims = prep_data(claims=claims, methods=args.methods)

    # Draw figure.
    fig = draw_map(
        claims=agg_claims,
        map=mapfile,
        corners=gridmap_corners,
        title=args.title,
        width=args.width,
    )

    # Output
    if ".html" in args.output:
        fig.write_html(args.output)
    else:
        fig.write_image(args.output)
    print(f"Finished. Claim map saved to {args.output}.")


def open_browser():
    webbrowser.open(
        f"http://{os.getenv('HOST', '127.0.0.1')}:{os.getenv('PORT', '8050')}/"
    )


def app_output(args, mapfile, gridmap_corners):
    # Scrape.
    if not args.noscrape:
        crawl(args.url, args.scrapefile)

    # Prepare the data.
    claims = pd.read_json(args.scrapefile)
    agg_claims = prep_data(claims=claims, methods=args.methods)

    app = make_app(
        agg_claims=agg_claims, claims=claims, mapfile=mapfile, corners=gridmap_corners
    )

    # We need to start a new thread to open the browser, since this the main one will
    #   be occupied running the app.
    Timer(1, open_browser).start()
    app.run(debug=args.debug)


def add_common_arguments(parser):
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
        "-s",
        "--scrapefile",
        default="interiors.json",
        help="JSON file to store scraping outputs in. Defaults to 'interiors.json'",
    )
    parser.add_argument(
        "--noscrape",
        action="store_true",
        help=(
            "Do not scrape the website. Expects and existing JSON file, specified "
            + "by --scrapefile."
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


def main():
    parser = argparse.ArgumentParser(
        prog="ptr-claim",
        description="Visualize interior claims on the Tamriel Rebuilt claims browser.",
    )
    add_common_arguments(parser)
    parser.add_argument(
        "-o",
        "--output",
        default="TR_int_claims.html",
        help=(
            "Output image filename. If the file extension is .html, the image will "
            + "be interactive. Extensions like .png, .jpeg, .webp, .svg, or .pdf will "
            + "result in a static image. Defaults to 'TR_int_claims.html'."
        ),
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
        "-d",
        "--debug",
        action="store_true",
        help="Show debug messages.",
    )
    parser.set_defaults(func=static_output)

    subparsers = parser.add_subparsers()
    app_parser = subparsers.add_parser("app")
    add_common_arguments(app_parser)
    app_parser.add_argument(
        "-t",
        "--title",
        default="Tamriel Rebuilt | Interior claims",
        help=(
            "Title of the output app. Defaults to 'Tamriel Rebuilt |"
            + " Interior claims'."
        ),
    )
    app_parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Show debug messages and reload the app upon code change.",
    )
    app_parser.set_defaults(func=app_output)

    args = parser.parse_args()

    # Set debug
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    # TO DO: make background map and coordinates configurable
    mapfile = os.path.join(
        os.path.dirname(__file__), "data", "Tamriel Rebuilt Province Map_2022-11-25.png"
    )
    gridmap_corners = "-42 61 -64 38"
    gridmap_corners = [int(c) for c in gridmap_corners.split()]

    args.func(args, mapfile=mapfile, gridmap_corners=gridmap_corners)


if __name__ == "__main__":
    main()
