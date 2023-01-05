import json
import logging
import os
import re
from urllib.request import urlopen
from urllib.error import HTTPError

import numpy as np
import pandas as pd
from PIL import Image
import pytesseract

from ptr_claim import data

# Mapping parameters
CELL_SIZE = 8192
_stages = [
    "Design",
    "Unclaimed",
    "Claim Pending",
    "In Development",
    "Pending Review",
    "Under Review",
    "Ready to Merge",
    "Merged",
]


def get_coords_from_image(url, crop_coords=(0, 0, 300, 35), upscale=2, **kwargs):
    """Fetch coordinates from an image on specified url using pytesseract.

    Args:
        url (str): url from which to find image.
        crop_coords (tuple, optional): Crop the image to find the cell coordinates.
         Defaults to (0, 0, 200, 50).
        upscale: Scaling a small image up often helps Tesseract.
        **kwargs: Passed to pytesseract.image_to_string.

    Returns:
        tuple(int, int|None, None): two cell coordinates, if found.
    """
    # Digit with optional minus (grp1), either a comma or point OR a space,
    # any number of optional spaces, another digit with minus (grp2).
    # OR, a separator of only a minus also works.
    cell_regex = r"(-?\d+)(?:(?:[,.]+|\s)\s?(-?\d+)|(-\d+))"

    logging.info(f"Fetching image at url: {url}.")
    try:
        image = Image.open(urlopen(url))
    except HTTPError:
        logging.debug(f"Could not access image.")
        return None, None
    image_small = image.crop(crop_coords)
    image_upscaled = image_small.resize(
        (image_small.width * upscale, image_small.height * upscale)
    )
    prediction = pytesseract.image_to_string(image_upscaled, **kwargs)
    try:
        matches = re.search(cell_regex, prediction).groups()
        # I couldn't figure out how to get the regex to return anything but three
        # groups, given I had to schemas for the second number. So, I just delete the
        # empty one for now.
        x, y = [match for match in matches if match]
        logging.debug(f"Found coordinates {(x, y)}.")
        return int(x), int(y)
    except AttributeError:
        logging.debug(f"Found no coordinates.")
        return None, None


def fill_coords_from_images(
    df,
    url_col="image_url",
    coord_cols=("cell_x", "cell_y"),
    na_only=True,
    **kwargs,
):
    """Fill specificed coordinate columns of Dataframe by reading coordinates from an
    image.

    Args:
        df (pandas.DataFrame): DataFrame containing claims and an url_col column.
        url_col (str, optional): df column name where the image URL is stored. Defaults
            to "image_url".
        coord_cols (tuple, optional): Tuple of two df column names where the resulting
            coordinates are stored. Defaults to ("cell_x", "cell_y").
        na_only (bool): Whether to fill only missing values in this method. Defaults to
            True.
        **kwargs: passed to get_coords_from_image
    """
    if na_only:
        mask = (df[coord_cols[0]].isna()) & (~df[url_col].isna())
        logging.debug(f"Only modifying empty coordinates with non-empty '{url_col}'.")
    else:
        logging.debug(f"Modifying all coordinates with non-empty '{url_col}'.")
        mask = ~df[url_col].isna()
    logging.debug(f"Modifying {df[mask].shape[0]} rows.")

    # Fetch known coordinate values from file.
    # with resources.open_binary(data, "img_coords.json") as coord_db_file:

    img_coord_path = os.path.join(os.path.dirname(__file__), "data", "img_coords.json")
    with open(img_coord_path) as coord_db_file:
        coord_db = json.load(coord_db_file)
        logging.debug(f"Using existing image coordinate database.")

    # Only fetch images that aren't in the database yet.
    requested_imgs = df.loc[mask, url_col].to_list()
    new_imgs = set([url for url in requested_imgs if url not in coord_db])
    if len(new_imgs) > 0:
        logging.debug(f"Fetching new coordinates for {len(new_imgs)} images.")
        for url in new_imgs:
            coord_db[url] = get_coords_from_image(url, **kwargs)

        # Print missing URLs
        logging.info("New coordinates found by OCR:")
        for url in new_imgs:
            logging.info(f"{url}: {coord_db[url]}")
    else:
        logging.debug("No new images needed.")

    # Add requested coordinates into the dataframe.
    df.loc[mask, coord_cols[0]] = df.loc[mask, url_col].apply(lambda x: coord_db[x][0])
    df.loc[mask, coord_cols[1]] = df.loc[mask, url_col].apply(lambda x: coord_db[x][1])


def fill_coords_from_hints(
    df, loc_dict, hint_col, coord_cols=("cell_x", "cell_y"), na_only=True
):
    """Fill specified coordinate columns of DataFrame by reading coordinates from hint
    tables.

    Args:
        df (pandas.DataFrame): DataFrame containing claims and a hint_col column.
        loc_dict (dict): dictionary containing hints a tuples of corresponding
            coordinates.
        hint_col (str, optional): df column name where hint is to be found.
        coord_cols (tuple, optional): Tuple of two df column names where the resulting
            coordinates are stored. Defaults to ("cell_x", "cell_y").
        na_only (bool): Whether to fill only missing values in this method. Defaults to
            True.
    """
    for hint in loc_dict:
        logging.debug(f"checking hint '{hint}' in '{hint_col}'")
        if na_only:
            logging.debug(
                f"Only modifying empty coordinates with matching '{hint_col}'."
            )
            mask = (df[coord_cols[0]].isna()) & df[hint_col].str.contains(
                hint, case=False
            )
        else:
            logging.debug(f"Modifying all coordinates with matching '{hint_col}'.")
            mask = df[hint_col].str.contains(hint, case=False)
        logging.debug(
            f"Modifying {df[mask].shape[0]} rows to coordinates {loc_dict[hint]}."
        )
        df.loc[mask, coord_cols] = loc_dict[hint]


def get_stage_mean(stages_iter):
    """Return the mean stage name from a list of stages.

    Args:
        stages_iter (iter): the stages to be averaged.

    Returns:
        str: The "mean" stage name.
    """
    enumdict = {stage: i for i, stage in enumerate(stages_iter)}
    reversedict = dict(enumerate(stages_iter))
    group_nums = [enumdict[stage] for stage in stages_iter]
    stage_mean = round(np.mean(group_nums))
    return reversedict[stage_mean]


def get_stage_counts(stages_list):
    """Return the types and counts of stages from a list of stages.

    Args:
        stages_list (iter): An iterable of stages to be analysed.

    Returns:
        tuple(list, list): Tuple containing a list of stages and a list of corresponding
            counts.
    """
    counts = pd.Series(stages_list).value_counts()
    # Sort values.
    sorted = counts.sort_index(key=lambda s: s.map(lambda x: _stages.index(x)))
    return list(sorted.index), list(sorted.values)


def make_nice_hovertext(x, url=False):
    if url:
        txt = f"<a href={x['url']}>{x['title']}</a>: {x['stage']}"
    else:
        txt = f"{x['title']}: {x['stage']}"
    if x["claimant"]:
        txt += f", claimant: {x['claimant']}"
    if x["reviewers"]:
        txt += f", reviewers: {x['reviewers']}"
    return txt


def locate_claims(claims, methods):

    if "i" in methods:
        # Use OCR to read missing cell coordinates.
        logging.info(f"Fetching images for all unlocated claims.")
        fill_coords_from_images(claims)
        logging.info(
            f"{claims[claims['cell_x'].isna()].shape[0]}"
            + " claims without coordinates after image analysis."
        )

    if "t" in methods:
        # Use known location names to guess missing cell coordinates.
        # with resources.open_binary(data, "name_hints.json") as namefile:
        name_hints_path = os.path.join(
            os.path.dirname(__file__), "data", "name_hints.json"
        )
        with open(name_hints_path) as namefile:
            name_hints = json.load(namefile)
        fill_coords_from_hints(claims, name_hints, "title")
        logging.info(
            f"{claims[claims['cell_x'].isna()].shape[0]}"
            + " claims without coordinates after known names accounted for."
        )

    if "e" in methods:
        # Fix Embers of Empire cell coordinates.
        itomask = (claims["title"].str.contains("[ITO]")) & (claims["cell_x"] > 100)
        claims.loc[itomask, "cell_x"] = claims.loc[itomask, "cell_x"] - 100
        logging.info(
            (
                f"Fixed {claims[itomask].shape[0]} claims that were transposed during "
                + "Embers of Empire development."
            )
        )

    if "u" in methods:
        # Use known urls to get missing cell coordinates for one-offs.
        # with resources.open_binary(data, "url_hints.json") as urlfile:

        url_hints_path = os.path.join(
            os.path.dirname(__file__), "data", "url_hints.json"
        )
        with open(url_hints_path) as urlfile:
            url_hints = json.load(urlfile)
        fill_coords_from_hints(claims, url_hints, "url", na_only=False)

    if claims[claims["cell_x"].isna()].shape[0] > 0:
        not_located = claims.loc[claims["cell_x"].isna(), "url"].tolist()
        logging.warning(
            f"{len(not_located)} claims not located: " + "\n".join(not_located)
        )
    else:
        logging.info("All claims located!")


def prep_data(claims, methods="itue"):

    logging.info(
        f"{claims[claims['cell_x'].isna()].shape[0]}"
        + " claims without coordinates after web scrape."
    )

    # Fill missing cell values.
    locate_claims(claims, methods)

    # Visualize only claims with known cell coordinates.
    located_claims = claims[~claims["cell_x"].isna()].copy()

    # Sort by stage.
    stages = [stage for stage in _stages if stage in claims["stage"].unique()]
    logging.debug("Imported claims include stages " + ", ".join(stages) + ".")
    located_claims["stage"] = located_claims["stage"].astype("category")
    located_claims["stage"] = located_claims["stage"].cat.set_categories(
        stages, ordered=True
    )
    located_claims = located_claims.sort_values(by="stage")

    # Generate readable description string
    located_claims["details"] = located_claims.apply(
        make_nice_hovertext, axis="columns"
    )

    # Group per cell
    grouped_claims = located_claims.groupby(["cell_x", "cell_y"])
    aggregated_claims = grouped_claims.aggregate(
        count=("title", "count"),
        details=("details", "\n".join),
        stage_mean=("stage", get_stage_mean),
        stage_groups=("stage", get_stage_counts),
    ).reset_index()

    # Coordinates in units, not cells, and count numbers larger
    aggregated_claims["cell_x_map"] = (
        aggregated_claims["cell_x"] * CELL_SIZE + CELL_SIZE / 2
    )
    aggregated_claims["cell_y_map"] = (
        aggregated_claims["cell_y"] * CELL_SIZE + CELL_SIZE / 2
    )
    # We want plotted counts to scale with area and in a logarithmic fashion.
    aggregated_claims["map_size"] = (np.log(aggregated_claims["count"]) + 1) * 30

    # Return usable data.
    return aggregated_claims
