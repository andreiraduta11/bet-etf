#!/usr/bin/env python3


from concurrent.futures import ThreadPoolExecutor
from json import dumps, loads
from math import floor
from multiprocessing import cpu_count
from socket import AF_INET, SOCK_STREAM, socket
from time import sleep
from traceback import print_exc
from typing import Dict, List

from mysql.connector import connect

# Constants used in program, especially in dictionaries.
PRICE = 'price'
SYMBOL = 'symbol'
WEIGHT = 'weight'
QUANTITY = 'quantity'


class Application:
    """
        This class represents a multi-threading server that will accept
        connections from visualizers and will calculate the amount of money for
        every symbol, using also informations from the MySQL database.
    """

    MYSQL_CONFIG = {
        'symbols_limit': 10,
        'retries': 30,
        'timeout': 1,
        'connect':  {
            'user': 'mysql_user',
            'password': 'mysql_resu_password',
            'database': 'mysql_database',
            'host': 'mysql',
        },
        'query': 'SELECT symbol, price, weight FROM symbols '
        + 'ORDER BY weight DESC LIMIT %s'
    }

    def __init__(
        self, host='0.0.0.0', port=3000, backlog=0, timeout=60, debug=False
    ) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self.debug = debug

        self.backlog = cpu_count() if not backlog else backlog

        self.executor = ThreadPoolExecutor(max_workers=self.backlog)

    def run(self) -> None:
        """
            Create a socket to communicate with the visualizers.
            For every connection, execute the thread_target in an other thread.
        """
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        self.socket.listen(self.backlog)

        while True:
            try:
                client, address = self.socket.accept()
                self.executor.submit(self.thread_target, client, address)

            except Exception:
                self.executor.shutdown()
                print_exc()

    def thread_target(self, client, address) -> None:
        """
            The workflow of a thread consists of:

            1) Get from the database an initial data about the index of format:
               {'symbol': {'price': <float_price>, 'weight': <float_weight>}}.

            2) The symbols are sorted by weight, resort them by name.

            3) Send the prices for every symbol, as initial data in table.

            4) Start the working loop, where there will received the data from
            the general_table and the symbols_table, calculate the amount of
            money to every symbol (so the data of the symbols_table) and send
            it back to the visualizer.
        """
        try:
            symbols = self.get_db_symbols()
            symbols = {symbol: symbols[symbol] for symbol in sorted(symbols)}

            symbols_weights = {
                symbol: item['weight'] for symbol, item in symbols.items()
            }

            symbols_init = [
                {
                    'symbol': symbol,
                    'price': item['price'],
                    'current-quantity': 0,
                    'buy-quantity': 0,
                    'order-value': 0,
                }
                for symbol, item in symbols.items()
            ]

            client.sendall(dumps(symbols_init).encode('utf-8'))

            while True:
                general_table = loads(client.recv(1024).decode('utf-8'))
                symbols_table = loads(client.recv(1024).decode('utf-8'))

                invest_amount = float(general_table[0]['invest-amount'])
                fee = float(general_table[0]['transaction-fee']) / 100.0

                self.calculate_symbols_amounts(
                    invest_amount, fee, symbols_table, symbols_weights
                )

                client.sendall(dumps(symbols_table).encode('utf-8'))

        except Exception:
            client.close()
            print_exc()

    def calculate_symbols_amounts(
        self, invest_amount: float, fee: float, symbols: List, weights: Dict
    ) -> List:
        """
            This function will make the calculus for every symbol.

            The symbols parameter contains a list with the details about each
            symbol in a dictionary, sorted by the symbols names.

            The idea is to calculate for a symbol:
            1) What is the current value in portfolio.
            2) What should be the value after this buy.

            Differences between target value and actual value will be calculated
            for every symbol and if the sum of the all differences:
                * is bigger than the invest_amount, scale those differences
                with the weights of the symbols and make only these purchases.
                * is smaller than the invest_amount, distribute the difference
                between to the amount of each symbol, according to the weights.
        """
        # Work with net value of the invest amount.
        invest_amount = invest_amount * (1 - fee)

        # Calculate the actual and the target value of portfolio.
        actual_portfolio = sum([
            item['price'] * item['current-quantity'] for item in symbols
        ])
        target_portfolio = actual_portfolio + invest_amount

        # Adapt the weights of the symbols because we work only with a part.
        # Let's say we cover 90% of the index. So mutiply with 1.1f.
        scale_factor = 2 - sum([weights[item['symbol']] for item in symbols])

        # The first iteration. Check for difference of target and actual.
        orders = {}

        for symbol, price, quant, _, _ in [list(it.values()) for it in symbols]:
            actual = quant * price
            target = target_portfolio * scale_factor * weights[symbol]

            difference = target - actual
            if difference > 0:
                orders[symbol] = difference

        # Make the sum of all the differences.
        diffs_sum = sum(orders.values())

        if diffs_sum < invest_amount:
            diffs_sum = invest_amount - diffs_sum

            # Spread the difference to all the symbols, but weighted.
            for symbol, order in orders.items():
                orders[symbol] += diffs_sum * scale_factor * weights[symbol]

        elif diffs_sum > 0:
            # Scale every difference according with the weights and budget.
            scale_factor = invest_amount / diffs_sum

            for symbol, order in orders.items():
                orders[symbol] = orders[symbol] * scale_factor

        # Calculate the exact values of the buying orders.
        # Make sure that is bigger than the minimum sum.
        if fee:
            minimum_order = 1.9 / fee
        else:
            minimum_order = 268

        # Sort the list by price, to use the remainders from each purchase.
        desc_price_symbols = sorted(
            symbols, key=lambda item: item['price'], reverse=True
        )

        while desc_price_symbols:
            symbol, price, current_quantity, _, _ = list(
                desc_price_symbols.pop(0).values()
            )

            invest_amount = orders.pop(symbol, 0)

            # Calculate the price, quantity and the value of the order.
            buy_quantity = floor(invest_amount / price)
            order_value = buy_quantity * price

            if order_value <= minimum_order:
                buy_quantity = 0
                order_value = 0

            # Calculate the value of remaining money after executing the
            # order for the current symbol. Distribute the rest to the others.
            invest_amount -= order_value

            # Distribute the remaining money to the rest of symbols.
            for key in orders:
                orders[key] += invest_amount / len(orders)

            for item in symbols:
                if item['symbol'] == symbol:
                    item['buy-quantity'] = buy_quantity
                    item['order-value'] = round(order_value * (1 + fee), 2)
                    break

        return symbols

    def get_db_symbols(self) -> Dict:
        """
            Get from database a dict with symbols and details about them.

            Feel free to change the query or the output format, if you need it,
            but pay attention that you will have to change the final format.

            The ouput is a dictionary:
                {'symbol': {'price': <float_price>, 'weight': <float_weight>}}.
        """
        symbols = {}
        connection = None

        # Try to get a connection and wait if the MySQL database is not ready.
        for index in range(Application.MYSQL_CONFIG['retries']):
            try:
                connection = connect(**Application.MYSQL_CONFIG['connect'])
                if connection and connection.is_connected():
                    break

            except Exception as exception:
                if index == Application.MYSQL_CONFIG['retries'] - 1:
                    raise exception
                else:
                    sleep(Application.MYSQL_CONFIG['timeout'])

        # Get the cursor for this MySQL connection.
        cursor = connection.cursor()
        if not cursor:
            connection.close()
            return symbols

        # Execute the query.
        cursor.execute(
            Application.MYSQL_CONFIG['query'],
            (Application.MYSQL_CONFIG['symbols_limit'], )
        )

        # Put the results in the desired form in a dictionary.
        for var in cursor:
            symbols.update({
                var[0]:  {PRICE: float(var[1]), WEIGHT: float(var[2]) / 100.0}
            })

        cursor.close()
        connection.close()
        return symbols


if __name__ == '__main__':
    Application().run()
