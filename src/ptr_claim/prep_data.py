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

# Mapping parameters
_stages = [
    "Design",
    "Unclaimed",
    "Claim Pending",
    "In Development",
    "Pending Review",
    "Under Review",
    "Ready to merge",
    "Merged",
]


def get_coords_from_image(url, crop_coords=(0, 0, 300, 35), upscale=2, **kwargs):
    """Fetch coordinates from an image on specified url using pytesseract.

    Args:
        url (str): URL from which to find image.
        crop_coords (tuple, optional): Crop the image to find the cell coordinates.
            Defaults to (0, 0, 200, 50), as that's where text is most times.
        upscale (int, optional): Factor to scale images by. Scaling a small image up
            often helps Tesseract.
        **kwargs: Passed to pytesseract.image_to_string.

    Returns:
        tuple(int, int|None, None): two cell coordinates, if found.
    """
    # Digit with optional minus (grp1), either a comma or point OR a space,
    # any number of optional spaces, another digit with minus (grp2).
    # OR, a separator of only a minus also works.
    cell_regex = r"(-?\d+)(?:(?:[,.]+|\s)\s?(-?\d+)|(-\d+))"

    logging.info(f"Fetching image at url: {url}")
    try:
        image = Image.open(urlopen(url))
    except HTTPError:
        logging.debug("Could not access image.")
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
        logging.debug("Found no coordinates.")
        return None, None


def add_url_hints_from_images(
    df,
    img_url_col="image_url",
    url_col="url",
    coord_cols=("cell_x", "cell_y"),
    **kwargs,
):
    """Populate the URL hints coordinate database with coordinates found on images.

    Args:
        df (pandas.DataFrame): DataFrame containing claims and an img_url_col column.
        img_url_col (str, optional): df column name where the image URL is stored.
            Defaults to "image_url".
        url_col (str, optional): df column name where the claim URL is stored. Defaults
            to "url".
        coord_cols (tuple, optional): Tuple of two df column names where the resulting
            coordinates are stored. Defaults to ("cell_x", "cell_y").
        **kwargs: passed to get_coords_from_image
    """
    # TODO: try to use importlib.resources or at least Pathlib
    url_hints_path = os.path.join(os.path.dirname(__file__), "data", "url_hints.json")
    with open(url_hints_path) as urlfile:
        url_hints = json.load(urlfile)
        logging.debug("Using URL coordinate hints database.")

    # Rows where coordinate is known, which aren't in the URL database and for which
    # there is an image.
    mask = (
        (df[coord_cols[0]].isna())
        & (~df[url_col].isin(url_hints.keys()))
        & (~df[img_url_col].isna())
    )

    def fill_url_dict_from_row(row, **kwargs):
        x, y = get_coords_from_image(row[img_url_col], **kwargs)
        if x is not None:
            logging.debug(
                f"Adding coordinates {x}, {y} to following claims:\n"
                + "\n".join(row[url_col])
            )
            for url in row[url_col]:
                url_hints[url] = [x, y]

    if df[mask].shape[0] > 0:
        # Fetch each image only once, apply resulting coordinates to all associated
        # URLs.
        grouped_img_urls = df.loc[mask, [url_col, img_url_col]].groupby(img_url_col)
        urls_per_img = grouped_img_urls[url_col].agg(list).to_frame().reset_index()
        logging.debug(
            f"Attempting to fetch coordinates for {df[mask].shape[0]} claims with "
            + f"images, {urls_per_img.shape[0]} unique images in total:"
        )
        urls_per_img.apply(fill_url_dict_from_row, axis="columns", **kwargs)
        with open(url_hints_path, "w") as urlfile:
            json.dump(url_hints, urlfile, indent=2)
    else:
        logging.debug("No images found to be queried.")


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
    enumdict = {stage: i for i, stage in enumerate(_stages)}
    reversedict = dict(enumerate(_stages))
    num_stages = [enumdict[stage] for stage in stages_iter]
    stage_mean = round(np.mean(num_stages))
    closest_to_mean = min(num_stages, key=lambda x: abs(x - stage_mean))
    # To avoid being-worked-on stuff from being hidden by default, bump mean stage up by
    # on "design" groups, if other stages are also present.
    if closest_to_mean == 0 and any(s > 0 for s in num_stages):
        nodesign = [s for s in stages_iter if s != "Design"]
        return get_stage_mean(nodesign)
    return reversedict[closest_to_mean]


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
    """Find or fix the coordinates for claims with missing coordinate data using a
    variety of methods.

    Args:
        claims (pandas.Dataframe): A dataframe of claims.
        methods (str): Methods for locating coordinates, one or several of "i", "u",
        "t", "e".
    """
    if "i" in methods:
        # Use OCR to read missing cell coordinates.
        logging.info("Fetching images for unlocated claims not in URL hint database.")
        add_url_hints_from_images(claims)

    if "u" in methods:
        # Use known urls to get missing cell coordinates for one-offs.
        # TODO: try to use importlib.resources or at least Pathlib
        url_hints_path = os.path.join(
            os.path.dirname(__file__), "data", "url_hints.json"
        )
        with open(url_hints_path) as urlfile:
            url_hints = json.load(urlfile)
        fill_coords_from_hints(claims, url_hints, "url", na_only=False)
        logging.info(
            f"{claims[claims['cell_x'].isna()].shape[0]}"
            + " claims without coordinates after URL hints accounted for."
        )

    if "t" in methods:
        # Use known location names to guess missing cell coordinates.
        # TODO: try to use importlib.resources or at least Pathlib
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

    if claims[claims["cell_x"].isna()].shape[0] > 0:
        not_located = claims.loc[claims["cell_x"].isna(), "url"].tolist()
        logging.warning(
            f"{len(not_located)} claims not located: \n" + "\n".join(not_located)
        )
        return claims[claims["cell_x"].isna()]

    logging.info("All claims located!")


def prep_data(claims, methods="itue"):
    logging.info(
        f"{claims[claims['cell_x'].isna()].shape[0]}"
        + " claims without coordinates after web scrape."
    )

    # Fill missing cell values.
    not_located = locate_claims(claims, methods)

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

    # We want plotted counts to scale with area and in a logarithmic fashion.
    # TODO: Make this nicer (so that two claims are differentiated form one, etc).
    aggregated_claims["map_size"] = (np.log(aggregated_claims["count"] + 1)) * 30

    # Return usable data and non-located stuff.
    return aggregated_claims, not_located
