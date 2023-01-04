import getpass
import re
import scrapy
from scrapy.crawler import CrawlerProcess
import argparse


class ScrapeTRSpider(scrapy.Spider):
    name = "scrape_tr"
    allowed_domains = ["www.tamriel-rebuilt.org"]
    start_urls = ["https://www.tamriel-rebuilt.org/user/login"]

    def parse(self, response):
        # Logs into the site (needed to see claimant, reviewer).
        return scrapy.FormRequest.from_response(
            response,
            formdata={"name": self.login, "pass": self.passwd},
            callback=self.after_login,
        )

    def after_login(self, response):
        ints_link = self.claims_page
        yield response.follow(ints_link, callback=self.parse_ints)

    def parse_ints(self, response):
        claim_row_path = "//tbody/tr"
        url_path = "td/a[contains(@href, 'claims')]"
        last_update_path = "td[contains(@class, 'last-updated')]/text()"
        # FOR TESTING
        # int_rows = response.xpath(claim_row_path)[:2]
        int_rows = response.xpath(claim_row_path)
        for row in int_rows:
            url = row.xpath(url_path)[0]
            last_update = row.xpath(last_update_path).get().strip()
            yield response.follow(
                url,
                callback=self.parse_claim_page,
                cb_kwargs=dict(last_update=last_update),
            )

        # Handle next pages
        next_page_path = "//li[contains(@class, 'pager-next')]/a"
        next_page = response.xpath(next_page_path)
        if next_page:
            yield response.follow(url=next_page[0], callback=self.parse_ints)

    def parse_claim_page(self, response, last_update):
        title_path = "//h1[contains(@id, 'page-title')]/text()"
        description_path = (
            "//article//div[contains(@class, 'claim-description')]//text()"
        )
        stage_path = (
            "//section[contains(@class, 'claim-stage')]"
            + "//section[contains(@class, 'claim-stage')]//li/text()"
        )
        claimant_path = (
            "//section[contains(@class, 'field-claimant')]"
            + "//section[contains(@class, 'field-claimant')]//a/text()"
        )
        reviewer_path = (
            "//section[contains(@class, 'field-reviewers')]"
            + "//section[contains(@class, 'field-reviewers')]//a/text()"
        )
        image_path = (
            "//div[contains(@class, 'claims-images')]"
            + "//a[contains(@class, 'colorbox')]/@href"
        )
        # Explanation for this regex:
        # Capture group 1: optional dash, then one or more digits.
        # One of either a comma or space, then an optional space or several.
        # Capture group 2: optional dash, then one or more digits.
        # Negative lookahead: can't follow with optional comma, optional space and
        #    one of either digit(s) or "and"
        cell_regex = r"(-?\d+)(?:,|\s)\s*(-?\d+)(?!,?\s?(?:\d+|and))"

        title = response.xpath(title_path).get()
        stage = response.xpath(stage_path).get()
        claimant = response.xpath(claimant_path).get()
        reviewers = response.xpath(reviewer_path).getall()
        reviewers = ", ".join(reviewers)
        description = response.xpath(description_path).getall()
        description = " ".join(description)
        image_url = response.xpath(image_path).get()
        # Cell numbers
        try:
            cell_x, cell_y = re.search(cell_regex, description).groups()
            cell_x, cell_y = int(cell_x), int(cell_y)
        except AttributeError:
            cell_x, cell_y = None, None

        yield dict(
            title=title,
            stage=stage,
            description=description,
            claimant=claimant,
            reviewers=reviewers,
            cell_x=cell_x,
            cell_y=cell_y,
            last_update=last_update,
            url=response.url,
            image_url=image_url,
        )


def fetch_credentials():
    """Get login credentials for the Tamriel Rebuilt website. Checks working directory
    for the file 'tr_secrets'. If not present, asks user on the command line.

    Returns:
        (str, str): login and password
    """
    try:
        from tr_secrets import login, passwd
    except ImportError:
        print("Enter credentials for tamriel-rebuilt.org.")
        login = input("Login name: ")
        passwd = getpass.getpass()
    return login, passwd


def start_crawl(url, outfile, crawler=ScrapeTRSpider, format="json"):
    """Runs the specified crawler on the specified webpage.

    Args:
        url (str): Claims browser page containing claims to be scraped.
        outfile (str): Output filepath.
        crawler (scrapy.Spider, optional): spider that starts the crawl. Defaults to
            ScrapeTRSpider.
        format (str, optional): Format of the output file. Defaults to "json".
    """
    process = CrawlerProcess(
        settings={
            "FEEDS": {
                f"{outfile}": {"format": format, "overwrite": True},
            },
            "ROBOTSTXT_OBEY": False,
        }
    )

    login, passwd = fetch_credentials()

    process.crawl(
        crawler,
        login=login,
        passwd=passwd,
        claims_page=url,
    )
    process.start()

def main():
    parser = argparse.ArgumentParser(
        prog="scrape-tr",
        description="Scrapes the Tamriel Rebuilt website for claims.",
    )
    parser.add_argument(
        "-i",
        "--input",
        default="https://www.tamriel-rebuilt.org/claims/interiors",
        help="Claims browser page containing claims to be scraped.",
    )
    parser.add_argument(
        "-o", "--output", default="interiors.json", help="Output json file."
    )
    args = parser.parse_args()

    start_crawl(args.input, args.output)


if __name__ == "__main__":
    main()
