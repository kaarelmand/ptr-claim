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
default, be output as an HTML file in the working directory. For more options, type
`ptr-claim -h`:

```
Visualize interior claims on the Tamriel Rebuilt claims browser.

optional arguments:
  -h, --help            show this help message and exit
  -u URL, --url URL     Claims browser page containing claims to be scraped. Defaults to 'https://www.tamriel-rebuilt.org/claims/interiors'.
  -o OUTPUT, --output OUTPUT
                        Output image filename. If the file extension is .html, the image will be interactive. Extensions like .png, .jpeg, .webp, .svg, or .pdf will result in a static image. Defaults to 'TR_int_claims.html'.
  -s SCRAPEFILE, --scrapefile SCRAPEFILE
                        JSON file to store scraping outputs in. Defaults to 'interiors.json'
  -w WIDTH, --width WIDTH
                        Output image width (px). Defaults to 1000.
  -t TITLE, --title TITLE
                        Title to be printed on the output. Defaults to 'Tamriel Rebuilt interior claims {date.today()}'.
  -M METHODS, --methods METHODS
                        How to locate missing claim coordinates. 'i' uses optical character recognition on claim images. 't' uses parts of the title to guess the coordinates. 'u' uses known URLs. 'e' fixes Embers of Empire coordinates. You can specify
                        several flags. Defaults to "itue".
```