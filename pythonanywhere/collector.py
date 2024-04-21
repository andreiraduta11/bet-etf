"""
    The module contains methods to collect data about the symbols of the BET
Index from the BVB and Tradeville websites.

    Andrei Răduță andrei.raduta11@gmail.com
"""

from datetime import datetime
from json import dump
from typing import Dict, List

from lxml.html import fromstring, HtmlElement
from pytz import timezone
from requests import get

BVB_URL: str = "https://www.bvb.ro/FinancialInstruments/Indices/IndicesProfiles.aspx"
BVB_XPATH: str = '//*[@id="gvC"]//tbody'


SYMBOL_URL: str = (
    "https://m.bvb.ro/FinancialInstruments/Details/FinancialInstrumentsDetails.aspx?s="
)


SYMBOLS_FILE_NAME: str = "symbols-data.json"
SYMBOLS_LIST_SIZE: int = 20


def collect_symbols_data(symbols_list_size: int) -> None:
    """
    Get the details of the *specified* first elements of the BET Index.
    Use the websites of the Bucharest Stock Exchange and Tradeville.

    The first element of the list will be the datetime of the operation.

    There are two steps. The result consists of a list of dictionaries.
    The keys are represented by the union of the following:
    1) Get the list of symbols with some information from BVB.
        0. symbol
        1. company
        2. shares
        3. price
        4. free_float_factor
        5. representation_factor
        6. price_correction_factor
        7. weight

    2) Get more details about every symbol from Tradeville website.
        1.  last_price
        3.  variation
        5.  open_price
        7.  max/min_price
        9.  medium_price
        11. volume
        13. dividend_yield

    The number before each key is the index of it in the raw data.
    """
    symbols_list: List[Dict[str, float]] = []

    # Get the list of symbols from the Bucharest Stock Exchange website.
    bvb_document = get_html_document(url=BVB_URL)

    # We have this in place because there are scenarios where the sum is bigger than 100.
    weight_total = 100.0

    # Extract the data of each cell (HTML TD) from each row (HTML TR).
    # Get the table with the symbols. Xpath returns a tbody, so parse it.
    for bvb_row in bvb_document.xpath(BVB_XPATH)[0][:symbols_list_size]:
        bvb_row = [data.text_content().strip() for data in bvb_row]

        # Get the more information from Tradeville using the symbol name.
        symbol_document = get_html_document(url=SYMBOL_URL + bvb_row[0])

        weight = min(round(float(bvb_row[7].replace(",", ".")), 2), weight_total)
        weight_total = round(weight_total - weight, 2)

        symbol_data: Dict[str, float] = {
            "symbol": bvb_row[0],
            "weight": weight,
            "shares": int(bvb_row[2].replace(".", "")),
            "company": bvb_row[1],
            "free_float_factor": float(bvb_row[4].replace(",", ".")),
            "representation_factor": float(bvb_row[5].replace(",", ".")),
            "price_correction_factor": float(bvb_row[6].replace(",", ".")),
        }

        for row in symbol_document.xpath('//*[@id="ctl00_body_upd"]/div[2]/div/div[1]')[
            0
        ][1][0]:
            if row[0].text == "Ultimul pret":
                symbol_data["buy_price"] = float(row[1][0].text.replace(",", "."))

            if row[0].text == "Pret deschidere":
                symbol_data["open_price"] = float(row[1][0].text.replace(",", "."))

            if row[0].text == "Pret maxim":
                symbol_data["max_price"] = float(row[1][0].text.replace(",", "."))

            if row[0].text == "Pret minim":
                symbol_data["min_price"] = float(row[1][0].text.replace(",", "."))

            if row[0].text == "Pret mediu":
                symbol_data["medium_price"] = float(row[1][0].text.replace(",", "."))

            if row[0].text == "Var (%)":
                symbol_data["variation"] = float(row[1][0].text.replace(",", "."))

        for row in symbol_document.xpath(
            '//*[@id="ctl00_body_ctl01_IndicatorsControl_dvIndicatori"]'
        )[0]:
            if "DIVY" in row[0].text:
                symbol_data["dividend_yield"] = float(row[1][0].text.replace(",", "."))

        # Build the list of symbols.
        symbols_list.append(symbol_data)

    # The first element will be the time of the update.
    symbols_list.insert(
        0, {"date": str(datetime.now(timezone("Europe/Bucharest"))).split(".")[0]}
    )

    with open(SYMBOLS_FILE_NAME, "w") as symbols_file:
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


if __name__ == "__main__":
    collect_symbols_data(symbols_list_size=SYMBOLS_LIST_SIZE)
