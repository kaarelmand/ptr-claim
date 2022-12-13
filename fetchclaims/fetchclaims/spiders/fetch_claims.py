import scrapy
import re


class FetchClaimsSpider(scrapy.Spider):
    name = "fetch_claims"
    allowed_domains = ["www.tamriel-rebuilt.org"]
    start_urls = ["http://www.tamriel-rebuilt.org/claims/interiors"]

    def parse(self, response):
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
            yield response.follow(url=next_page[0], callback=self.parse)

    def parse_claim_page(self, response, last_update):
        title_path = "//h1[contains(@id, 'page-title')]/text()"
        description_path = (
            "//article//div[contains(@class, 'claim-description')]//text()"
        )
        stage_path = "//section[contains(@class, 'claim-stage')]//li/text()"
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
            cell_x=cell_x,
            cell_y=cell_y,
            last_update=last_update,
            url=response.url,
            image_url=image_url,
        )
