#!/usr/bin/env python3


"""
    The module contains the instance of the DashApplication.
    Here is defined the callback for this instance that will update the
application information when changes from the user are received.

    Andrei Răduță andrei.raduta11@gmail.com
"""

from typing import Dict, List

from dash.dependencies import Input, Output, State

from dash_application import DashApplication

HOST = '0.0.0.0'
PORT = 8050

# For deployment, application.server (which is the actual flask app) for WSGI.
application = DashApplication()


@application.callback(
    [
        Output('symbols_time', 'children'),
        Output('symbols_datatable', 'data')
    ],
    [
        Input('symbols_list_size', 'value'),
        Input('invest_amount', 'value'),
        Input('transaction_fee', 'value'),
        Input('symbols_datatable', 'data_timestamp')
    ],
    [
        State('symbols_datatable', 'data')
    ]
)
def symbols_datatable_callback(
    symbols_list_size,
    invest_amount,
    transaction_fee,
    symbols_data_timestamp,
    symbols_data
) -> List[Dict]:
    """
        This callback runs whenever the user changes data in the Financials or
    Symbols DataTables. This method interacts with the Collector and Calculator
    modules of the project:
        * If the symbols_list_size has a new value, collect the new symbols.
        * Call the calculate_orders method to establish what orders are made.

        The tables are lists of dictionaries representating the rows.
        This representation is also used in Application object, so the return
    value will be its inner list of symbols with their details.
    """
    # If the size of the list has changed, get the information of the symbols.
    if len(application.get_symbols_list()) != symbols_list_size:
        application.collect_symbols_data(symbols_list_size)

    elif symbols_data:
        application.set_symbols_list(symbols_list=symbols_data)

    application.set_invest_amount(invest_amount)
    application.set_transaction_fee(transaction_fee)

    application.calculate_orders()

    return application.get_symbols_time(), application.get_symbols_list()


application.collect_symbols_data()

application.html_init_layout()

application.run_server(host=HOST, port=PORT, debug=True)
