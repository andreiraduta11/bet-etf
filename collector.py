#!/usr/bin/python3


from json import dump
from typing import List

from lxml.html import HtmlElement, fromstring
from requests import get

BVB_URL: str = (
    'https://www.bvb.ro/FinancialInstruments/Indices/IndicesProfiles.aspx'
)
BVB_XPATH: str = '//*[@id="gvC"]//tbody'


TRADEVILLE_URL: str = 'https://www.tradeville.eu/actiuni/actiuni-'
TRADEVILLE_XPATH: str = '//div[@class="quotationTblLarge"]'


SYMBOLS_FILE_NAME = 'symbols-data.json'
SYMBOLS_LIST_SIZE = 17


def collect_symbols_data(symbols_list_size: int) -> None:
    """
        Get the details of the *specified* first elements of the BET Index.
        Use the websites of the Bucharest Stock Exchange and Tradeville.

        There are two steps. The result consists of a list of dictionaries.
        The keys are represented by the union of the following:

        1) Get the list of symbols with some information from BVB.
            0. symbol.
            1. company.
            2. shares.
            3. price.
            4. free float factor.
            5. representation factor.
            6. price correction factor.
            7. weight.

        2) Get more details about every symbol from Tradeville website.
            1. last price.
            3. variation.
            5. open price.
            7. max/min price.
            9. medium price.
            11. volume.
            13. dividend yield.

        The number before each key is the index of it in the raw data.
    """
    symbols_list: List = []

    bvb_document = get_html_document(url=BVB_URL)

    # Extract the data of each cell (HTML TD) from each row (HTML TR).
    # Get the table with the symbols. Xpath returns a tbody, so parse it.
    for bvb_row in bvb_document.xpath(BVB_XPATH)[0][:symbols_list_size]:
        bvb_row = [data.text_content().strip() for data in bvb_row]

        # Get the more information from Tradeville using the symbol name.
        tradeville_document = get_html_document(
            url=TRADEVILLE_URL + bvb_row[0]
        )

        for trv_row in tradeville_document.xpath(TRADEVILLE_XPATH):
            trv_row = [data.text_content().strip() for data in trv_row]

            # Some yields are 'n/a'.
            try:
                dividend_yield = float(trv_row[13].replace('%', ''))
            except Exception:
                dividend_yield = 0

            # Build the list of symbols.
            symbols_list.append({
                'symbol': bvb_row[0],
                'weight': float(bvb_row[7]),
                'open_price': float(trv_row[5]),
                'buy_price': float(trv_row[1]),
                'variation': float(trv_row[3].replace('%', '')),
                'medium_price': float(trv_row[9]),
                'min_price': float(trv_row[7].split('/')[1]),
                'max_price': float(trv_row[7].split('/')[0]),
                'dividend_yield': dividend_yield,
                'volume': int(trv_row[11].replace(',', '')),
                'shares': int(bvb_row[2].replace(',', '')),
                'company': bvb_row[1],
                'free_float_factor': float(bvb_row[4]),
                'representation_factor': float(bvb_row[5]),
                'price_correction_factor': float(bvb_row[6]),
            })

            # Select only the first column from Tradeville.
            break

    with open(SYMBOLS_FILE_NAME, 'w') as symbols_file:
        dump(symbols_list, symbols_file)


def get_html_document(url: str) -> HtmlElement:
    """
        Get the HTML document of a web page and parse it using lxml module.

        If the response failed, an Exception will be raised.
        Further, the information will be extracted using xpath.
    """
    response = get(url)
    response.raise_for_status()

    return fromstring(response.content)


if __name__ == '__main__':
    collect_symbols_data(symbols_list_size=SYMBOLS_LIST_SIZE)
