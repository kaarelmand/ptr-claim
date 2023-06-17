# ptr-claim

Scrape the Tamriel Rebuilt and Project Tamriel websites and visualize claim progress.
Currently only works with interior claims on the Tamriel Rebuilt website claims browser.

## Installation

1. Make sure you have python version 3.7 or higher installed and that python is
   added to your PATH (i.e., accessible from the command line). For Windows,
   [see instructions here](https://datatofish.com/add-python-to-windows-path/).
2. Install the Tesseract OCR (optical character recognition) engine -- see the
   [install instructions](https://tesseract-ocr.github.io/tessdoc/Installation.html).
   On Windows, grab the binary from
   [the UB Mannheim site](https://github.com/UB-Mannheim/tesseract/wiki#tesseract-installer-for-windows)).
3. On the command line, type `pip install ptr-claim`. This should download the program
   and all required dependencies.
4. On Windows, you will additionally need to install
   [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/).

## Usage

Open the command line and type `ptr-claim`. You will be asked for your Tamriel Rebuilt
website login and password. This is only needed to populate the claimant and reviewer
fields. If those aren't needed, you can enter empty values. The end result will, by
default, be output as an HTML file in the working directory.

Options can be left default for most purposes. If you do want to customize, then options can be passed using environment variables:
- PTR_TR_LOGIN and PTR_TR_PASSWD -- The username and password for
  www.tamriel-rebuilt.org. If not present, the user is prompted to enter the 
  credentials on the command line.
- PTR_SCRAPESWITCH -- `false` or `true` (default). Whether to run the scraper. If
  `false`, a JSON scrapefile must already be present.
- PTR_URL -- Claims browser URL containing claims to be scraped. Defaults to 
  `https://www.tamriel-rebuilt.org/claims/interiors`.
- PTR_SCRAPEFILE -- JSON file to store scraping outputs in, relative to the `data`
   directory in the install directory. Defaults to `interiors.json`.
- PTR_METHODS -- How to locate missing claim coordinates.
  - 'i' uses optical character recognition on claim images.
  - 't' uses parts of the title to guess the coordinates.
  - 'u' uses known URLs. 
  - 'e' fixes Embers of Empire coordinates.
  You can specify several flags. Defaults to `itue`.
- PTR_MAPFILE -- Image file to use as background, relative in the `data` directory
  in the install directory. Defaults to `Tamriel Rebuilt Province Map_2022-11-25.png`.
- PTR_MAPCORNERS -- Cell coordinates for the corners of the background image file.
  Expects four integers separated by spaces: `X_left X_right Y_bottom Y_top`. Defaults
  to `-42 61 -64 38`.
- PTR_WIDTH -- Output image width (px). Defaults to 1000.