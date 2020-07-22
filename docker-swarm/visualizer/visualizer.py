#!/usr/bin/env python3


from json import dumps, loads
from socket import AF_INET, SOCK_STREAM, socket

from dash import Dash
from dash.dependencies import Input, Output, State
from dash_html_components import Div
from dash_table import DataTable
from dash_table.Format import Format, Group, Scheme, Sign, Symbol

"""
    Configurations of the implied servers.
"""
VISUALIZER_PORT = 8050
VISUALIZER_ADDRESS = '0.0.0.0'

SERVER_ADDRESS = ('server', 30000)


"""
    Create the Dash application and the socket for server communication.
"""
application = Dash(__name__)
server_socket = socket(AF_INET, SOCK_STREAM)


@application.callback(
    Output('symbols-table', 'data'),
    [Input('general-table', 'data'), Input('symbols-table', 'data_timestamp')],
    [State('symbols-table', 'data')]
)
def update_symbols_table(general_table, timestamp, symbols_table):
    """
        The `rows` parameters will contain in the `output-data` the new data.
        Get all this new data and send it to the server to make the calculus.
    """
    for row in general_table:
        for value in row.values():
            if value != 0 and not value:
                return symbols_table

    for row in symbols_table:
        for value in row.values():
            if value != 0 and not value:
                return symbols_table

    try:
        server_socket.sendall(dumps(general_table).encode('utf-8'))
        server_socket.sendall(dumps(symbols_table).encode('utf-8'))
        symbols_table = loads(server_socket.recv(1024).decode('utf-8'))
    except Exception:
        server_socket.close()
        server_socket.connect(SERVER_ADDRESS)

    return symbols_table


if __name__ == '__main__':
    """
        Here is described the workflow of the visualizer.
        It is not a class because of the usage of decorators for functions.

        1) Get the initial data for the symbols-table from the server.

        2) Create the application layout:
            * table with general information:
                - amount of money to be invested.
                - percentage of the transaction fee.
            * table with the list of symbols:
                - symbol.
                - price (requested for the transaction).
                - quantity (currently in the portfolio).
                - order value (includes transaction fee).
    """
    # Get the initial data from the server.
    server_socket.connect(SERVER_ADDRESS)
    symbols_table_data = loads(server_socket.recv(1024).decode('utf-8'))

    application.layout = Div([
        Div(
            [DataTable(
                id='general-table',
                columns=[
                    {
                        'format': Format(precision=2, scheme=Scheme.fixed),
                        'id': 'invest-amount',
                        'name': 'Invest Amount (RON)',
                        'type': 'numeric',
                    },
                    {
                        'format': Format(precision=2, scheme=Scheme.fixed),
                        'id': 'transaction-fee',
                        'name': 'Transaction Fee (%)',
                        'type': 'numeric',
                    },
                ],
                data=[{'invest-amount': 4900.0, 'transaction-fee': 0.71}],
                style_cell={'min-width': '150px'},
                editable=True,
            )],
            style={'padding': '10px', 'float': 'left'},
        ),
        Div(
            [DataTable(
                id='symbols-table',
                columns=[
                    {
                        'editable': False,
                        'id': 'symbol',
                        'name': 'Symbol',
                    },
                    {
                        'format': Format(precision=4, scheme=Scheme.fixed),
                        'id': 'price',
                        'name': 'Price (RON)',
                        'type': 'numeric',
                    },
                    {
                        'format': Format(precision=0, scheme=Scheme.fixed),
                        'id': 'current-quantity',
                        'name': 'Current Quantity',
                        'type': 'numeric',
                    },
                    {
                        'format': Format(precision=0, scheme=Scheme.fixed),
                        'id': 'buy-quantity',
                        'name': 'Buy Quantity',
                        'type': 'numeric',
                    },
                    {
                        'format': Format(precision=2, scheme=Scheme.fixed),
                        'id': 'order-value',
                        'name': 'Order Value (RON)',
                        'type': 'numeric',
                    },
                ],
                data=symbols_table_data,
                style_cell={'min-width': '150px'},
                editable=True,
            )],
            style={'padding': '10px', 'float': 'left'},
        ),
    ])

    application.run_server(host=VISUALIZER_ADDRESS, port=VISUALIZER_PORT)
