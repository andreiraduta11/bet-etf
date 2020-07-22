#!/usr/bin/env python3


from sys import exit
from time import sleep
from typing import Dict, List

from lxml.html import HtmlElement, fromstring
from requests import get

from mysql.connector import connect

LOOP_INTERVAL = 1 * 60

MYSQL_TIMEOUT = 3
MYSQL_RETRIES = 10
MYSQL_CONFIG = {
    'user': 'mysql_user',
    'password': 'mysql_resu_password',
    'database': 'mysql_database',
    'host': 'mysql',
}


SYMBOLS_LIST_SIZE = 17


BVB_URL: str = (
    'https://www.bvb.ro/FinancialInstruments/Indices/IndicesProfiles.aspx'
)
BVB_XPATH: str = '//*[@id="gvC"]//tbody'


TRADEVILLE_URL: str = 'https://www.tradeville.eu/actiuni/actiuni-'
TRADEVILLE_XPATH: str = '//div[@class="quotationTblLarge"]'


class Collector:
    def run(self) -> None:
        """
            Here is described the workflow of this service:

            1 - get the symbols of the index and their weights from BVB.
            2 - get more details about every symbol from Tradeville broker.
        """
        while True:
            symbols_list = []

            # Get the symbols of the BET index from Bucharest Stock Exchange.
            try:
                symbols_list = Collector.get_symbols_list()

            except Exception as exception:
                exit(
                    'Exception occurred trying to get data from BVB:\n'
                    + str(exception)
                )

            # Insert or update the symbols into the MySQL database.
            try:
                Collector.update_mysql_symbols_table(symbols_list)

            except Exception as exception:
                exit(
                    'Exception occurred trying to update table in MySQL:\n'
                    + str(exception)
                )

            sleep(LOOP_INTERVAL)

    @staticmethod
    def get_symbols_list(
        symbols_list_size: int = SYMBOLS_LIST_SIZE
    ) -> List[Dict]:
        """
            Get the details of the *specified* first elements of the BET Index.
            Use the websites of the Bucharest Stock Exchange and Tradeville.

            The first element of the list will be the time of the operation.

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
        symbols_list: List[Dict] = []

        # Get the list of symbols from the Bucharest Stock Exchange website.
        bvb_document = Collector.get_html_document(url=BVB_URL)

        # Extract the data of each cell (HTML TD) from each row (HTML TR).
        # Get the table with the symbols. Xpath returns a tbody, so parse it.
        for bvb_row in bvb_document.xpath(BVB_XPATH)[0][:symbols_list_size]:
            bvb_row = [data.text_content().strip() for data in bvb_row]

            # Get the more information from Tradeville using the symbol name.
            tradeville_document = Collector.get_html_document(
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
                    'weight': float(bvb_row[7]) / 100.0,
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

                # Select only the first column from the Tradeville info table.
                break

        return symbols_list

    @staticmethod
    def get_html_document(url: str) -> HtmlElement:
        """
            Get the HTML page from an URL.
            From that page return an HtmlElement structure.

            If the response failed, an Exception will be raised.
        """
        response = get(url)
        response.raise_for_status()

        return fromstring(response.content)

    @staticmethod
    def update_mysql_symbols_table(symbols_list: List[Dict]) -> None:
        """
            Update the table from MySQL that is holding symbols informations.
            *** The insert is based on the order of fields in the dictionary.
        """
        connection = None

        for index in range(MYSQL_RETRIES):
            try:
                connection = connect(**MYSQL_CONFIG)
                if connection and connection.is_connected():
                    break

            except Exception as exception:
                if index == MYSQL_RETRIES - 1:
                    raise exception
                else:
                    sleep(MYSQL_TIMEOUT)

        cursor = connection.cursor()
        if not cursor:
            connection.close()
            return

        query = (
            'REPLACE INTO symbols ('
            'symbol, weight, open_price, buy_price, variation, medium_price,'
            'min_price, max_price, dividend_yield, volume, shares, company, '
            'free_float_factor, representation_factor, price_correction_factor'
            ') VALUES '
            '(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
        )

        for symbol_dict in symbols_list:
            cursor.execute(query, tuple(symbol_dict.values()))

        connection.commit()
        cursor.close()
        connection.close()


if __name__ == '__main__':
    Collector().run()
