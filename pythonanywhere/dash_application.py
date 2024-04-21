"""
    The module contains the Dash application with which the user will interact.

    The workflow consists of:
    1.  Build the HTML page using dash_html_components.
    2.  Update the Symbols DataTable using a callback.
        * The callback runs whenever data from the Financials or the Symbols DataTables has changed.
        * A special case is when the user changes the size of the list. Then, a new list is fetched
        using the Collector and the table resets.

    More information about Dash at: https://dash.plotly.com/datatable/reference.

    Andrei Răduță andrei.raduta11@gmail.com
"""

from json import loads
from typing import Any, Dict, List

import requests
from dash import Dash
from dash_core_components import Input, Link
from dash_html_components import B, Div, H1, H2, I, Li, Ol, Table, Td, Tr, Ul
from dash_table import DataTable
from dash_table.Format import Format, Scheme


SYMBOLS_LIST_SIZE = 20

INVEST_AMOUNT = 10000
TRANSACTION_FEE = 0.49
MINIMUM_ORDER_VALUE = 310


DATA_URL: str = (
    "https://raw.githubusercontent.com/andreiraduta11/bet-etf/master/"
    "pythonanywhere/symbols-data.json"
)


class DashApplication(Dash):
    def __init__(self) -> None:
        super().__init__()

        self.symbols_time = ""
        self.symbols_list = []
        self.invest_amount = INVEST_AMOUNT
        self.transaction_fee = TRANSACTION_FEE

    def calculate_orders(self) -> None:
        """
        Calculate what quantity of each symbol to buy.
        It uses the internal symbols list of dictionaries.

        The algorithm works on:
        1) What is the current value of a symbol within the portfolio.
        2) What should be the value after these new purchases.

        Differences between the target value and actual value are calculated.
        If the sum of all these differences:
        1) is bigger than amount -> scale the differences with the weights
            of the involved symbols and buy only those;
        2) is smaller than amount -> distribute the difference between the
            sum allocated to each symbol, according to their weights.

        This process is done in 2 iterations.
        """
        actual_portfolio = 0
        for s in self.symbols_list:
            actual_portfolio += s.get("buy_price", 0) * s.get("current_quantity", 0)
        target_portfolio = actual_portfolio + self.invest_amount
        print(f"The actual_portfolio is {actual_portfolio}.", flush=True)

        # Adapt the weights, because not all the index symbols are included.
        # If 90% of the index is covered, multiplty each weight by (1/0.9).
        scale_factor = 1.0 / sum(
            [s.get("weight", 0) / 100.0 for s in self.symbols_list]
        )

        # Find the item most further away from what it should actually be. Then we calculate
        # the target portfolio based on that for us to understand what we should buy forward.
        difference_min = 0
        for s in self.symbols_list:
            # Update the weight, considering the new scale_factor.
            weight = s["weight"]
            weight_buy = weight * scale_factor / 100.0
            s.update({"weight": weight, "weight_buy": weight_buy * 100.0})

            value_now = s.get("buy_price", 0) * s.get("current_quantity", 0)
            value_fut = actual_portfolio * weight_buy

            if (difference := value_fut - value_now) and (difference_min > difference):
                target_portfolio = value_now / weight_buy
                difference_min = difference
        print(f"The target_portfolio is {target_portfolio}.", flush=True)

        # First iteration. Check for differences. Add if they are positive.
        symbol_to_buy_value: Dict[str, float] = {}

        # Calculate the normalized value to buy, normalizing to the self.invest_amount.
        # Calculate first how much we need more of a symbol to reach the target.
        total_value_buy: float = target_portfolio - actual_portfolio
        total_value_extra: float = max(0, self.invest_amount - total_value_buy)
        for s in self.symbols_list:
            weight_buy = s["weight_buy"] / 100.0
            value_buy = (target_portfolio * weight_buy) - (
                s.get("buy_price", 0) * s.get("current_quantity", 0)
            )

            if total_value_extra:
                difference = value_buy + total_value_extra * weight_buy
            else:
                difference = value_buy / total_value_buy * self.invest_amount

            if difference > 0:
                symbol_to_buy_value[s.get("symbol")] = difference

        print(f"To buy after 1st pass: {symbol_to_buy_value}.", flush=True)

        # First, eliminate the orders that cannot be done because of fee.
        symbols_heap = sorted(self.symbols_list, key=lambda s: s.get("weight"))
        while symbols_heap:
            # Get the next symbol with the lowest weight.
            symbol = symbols_heap.pop(0)
            symbol_name = symbol["symbol"]

            # Get its current allocated amount of money for purchase.
            buy_price = symbol.get("buy_price", 0)
            buy_value = symbol_to_buy_value.get(symbol.get("symbol"), 0)

            # Make transaction fee-efficient.
            if (buy_value // buy_price) * buy_price <= MINIMUM_ORDER_VALUE:
                symbol_to_buy_value.pop(symbol.get("symbol"), 0)

                # Distribute the money to the remaining symbols.
                total_to_buy = sum(symbol_to_buy_value.values())
                for key in symbol_to_buy_value.keys():
                    symbol_to_buy_value[key] += buy_value * (
                        symbol_to_buy_value[key] / total_to_buy
                    )

        print(f"To buy after 2nd pass: {symbol_to_buy_value}.", flush=True)

        # Calculate the exact values of the buying orders.
        # Sort the list by price, to use the remainders from each purchase.
        symbols_heap = sorted(
            self.symbols_list, key=lambda s: s.get("buy_price"), reverse=True
        )
        print(symbol_to_buy_value)
        while symbols_heap:
            # Get the next symbol with the biggest price.
            symbol = symbols_heap.pop(0)
            symbol_name = symbol["symbol"]

            # Get its current allocated amount of money for purchase.
            buy_price = symbol.get("buy_price", 0)
            buy_value = max(
                0,
                (symbol_to_buy_value.pop(symbol_name, 0) - 1.49)
                * (1 - self.transaction_fee / 100.0),
            )
            # Calculate the price, quantity and the value of the order.
            if buy_price:

                buy_quantity = buy_value // buy_price
                order = {
                    "buy_price": buy_price,
                    "buy_quantity": buy_quantity,
                    "order_value": round(
                        buy_quantity * buy_price * (1 + self.transaction_fee / 100.0)
                        + 1.49,
                        2,
                    ),
                    "symbol": symbol_name,
                }
            else:
                order = {}

            # Make transaction fee-efficient.
            if order.get("order_value") <= MINIMUM_ORDER_VALUE:
                order = {"buy_quantity": 0, "order_value": 0}
            else:
                print(order)

            # Calculate the value of remaining money after executing the
            # order for the current symbol. Distribute the rest to the others.
            remaining = buy_value - order.get("order_value")

            # Distribute the remainder from this purchase.
            total_to_buy = sum(symbol_to_buy_value.values())
            for key in symbol_to_buy_value.keys():
                symbol_to_buy_value[key] += remaining * (
                    symbol_to_buy_value[key] / total_to_buy
                )

            # Update the columns in the table.
            for item in self.symbols_list:
                if item["symbol"] == symbol_name:
                    item.update(order)
                    break

        self.symbols_list = sorted(self.symbols_list, key=lambda s: s.get("symbol"))

    def collect_symbols_data(self, symbols_list_size: int = SYMBOLS_LIST_SIZE) -> None:
        """
        Get the details of each symbol from the web.
        Fetch data a personal GitHub file (temporary solution).
        Use the update-symbols-data.sh script to update that public file.
        Use this because PythonAnywhere whitelist for GET requests.
        """
        response = requests.get(DATA_URL)
        response.raise_for_status()

        self.symbols_time = loads(response.content)[0].get("date")
        self.symbols_list = loads(response.content)[1 : symbols_list_size + 1]

    def html_init_layout(self) -> None:
        """
        Init the layout of the web page of the application.
        The layout consists of Instructions, Financials, and Symbols divs.
        """
        DIV_STYLE = {
            "clear": "both",
            "float": "left",
            "padding": "10px",
        }

        self.layout = Div(
            [
                Div(self.html_instruction_list(), style=DIV_STYLE),
                Div(self.html_financials_inputs(), style=DIV_STYLE),
                Div(self.html_symbols_datatable(), style=DIV_STYLE),
            ]
        )

    def html_instruction_list(self) -> List:
        return [
            H1("BET ETF Calculator"),
            Ul(
                [
                    Li("Andrei Răduță"),
                    Li("andrei.raduta11@gmail.com"),
                    Li(
                        Link(
                            children="https://github.com/andreiraduta11/bet-etf",
                            href="https://github.com/andreiraduta11/bet-etf",
                        )
                    ),
                ]
            ),
            H2("Instructions:"),
            Ol(
                [
                    Li("Set the size of the list of symbols."),
                    Li("Set the sum you are going to invest."),
                    Li("Set the specific transaction fee for your grid."),
                    Li(
                        [
                            "Set your current holdings for each symbol ",
                            I("(no information is stored)."),
                        ]
                    ),
                    Li(
                        (
                            "The buying price is the last price (at the specified "
                            "time). Feel free to change it."
                        )
                    ),
                    Li("Place your orders. The order values should be the same."),
                ]
            ),
            I(id="symbols_time"),
        ]

    def html_financials_inputs(self) -> Table:
        return Table(
            [
                Tr(
                    [
                        Td(B("Symbols List Size")),
                        Input(
                            debounce=True,
                            id="symbols_list_size",
                            max=SYMBOLS_LIST_SIZE,
                            min=1,
                            required=True,
                            step=1,
                            type="number",
                            value=SYMBOLS_LIST_SIZE,
                        ),
                    ]
                ),
                Tr(
                    [
                        Td(B("Invest Sum (RON)")),
                        Input(
                            debounce=True,
                            id="invest_amount",
                            min=0,
                            required=True,
                            type="number",
                            value=INVEST_AMOUNT,
                        ),
                    ]
                ),
                Tr(
                    [
                        Td(B("Transaction Fee (%)")),
                        Input(
                            debounce=True,
                            id="transaction_fee",
                            min=0,
                            required=True,
                            type="number",
                            value=TRANSACTION_FEE,
                        ),
                    ]
                ),
            ]
        )

    def html_symbols_datatable(self) -> DataTable:
        return DataTable(
            id="symbols_datatable",
            columns=[
                {
                    "id": "symbol",
                    "name": "Symbol",
                    "editable": False,
                    "type": "text",
                },
                self.html_number_datatable_cell(
                    id="weight",
                    name="Index Weight (%)",
                    precision=2,
                ),
                self.html_number_datatable_cell(
                    id="current_quantity",
                    name="Current Quantity",
                    editable=True,
                ),
                self.html_number_datatable_cell(
                    id="variation",
                    name="Price Variation (%)",
                    precision=4,
                ),
                self.html_number_datatable_cell(
                    id="medium_price",
                    name="Medium Price (RON)",
                    precision=4,
                ),
                self.html_number_datatable_cell(
                    id="buy_price",
                    name="Buy Price (RON)",
                    editable=True,
                    precision=4,
                ),
                self.html_number_datatable_cell(
                    id="buy_quantity",
                    name="Buy Quantity",
                ),
                self.html_number_datatable_cell(
                    id="order_value",
                    name="Order Value (RON)",
                    precision=2,
                ),
            ],
            editable=True,
            style_cell={"min-width": "150px"},
            style_data_conditional=[
                {
                    "if": {"filter_query": "{variation} < 0", "column_id": "variation"},
                    "color": "red",
                    "fontWeight": "bold",
                },
                {
                    "if": {
                        "filter_query": "{variation} >= 0",
                        "column_id": "variation",
                    },
                    "color": "green",
                    "fontWeight": "bold",
                },
            ],
            style_header_conditional=[
                {"fontWeight": "bold"},
                {"if": {"column_editable": True}, "color": "red"},
            ],
        )

    def html_number_datatable_cell(
        self,
        id: str,
        name: str,
        editable: bool = False,
        precision: int = 0,
        default: int = 0,
    ) -> Dict[str, Any]:
        """
        Create a Dash DataTable cell with type number.
        """
        return {
            "editable": editable,
            "format": Format(precision=precision, scheme=Scheme.fixed),
            "id": id,
            "name": name,
            "on_change": {"failure": "default"},
            "type": "numeric",
            "validation": {"default": default},
        }

    def get_symbols_time(self) -> str:
        if not self.symbols_time:
            return ""

        return f"The prices have been updated at {self.symbols_time}."

    def get_symbols_list(self) -> List[Dict]:
        return self.symbols_list if self.symbols_list else []

    def set_symbols_list(self, symbols_list: List[Dict]) -> None:
        self.symbols_list = symbols_list

    def set_invest_amount(self, invest_amount: float) -> None:
        self.invest_amount = invest_amount

    def set_transaction_fee(self, transaction_fee: float) -> None:
        self.transaction_fee = transaction_fee


if __name__ == "__main__":
    app = DashApplication()
    app.calculate_orders()
