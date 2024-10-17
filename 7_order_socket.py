
import credentials as crs
from fyers_apiv3 import fyersModel
import pandas as pd
import datetime as dt
#credentials
# Replace these values with your actual API credentials
client_id = crs.client_id
secret_key = crs.secret_key
redirect_uri = crs.redirect_uri
with open('access.txt') as f:
    access_token=f.read()



# Replace the sample access token with your actual access token obtained from Fyers
new_access_token = f"{client_id}:{access_token}"


from fyers_apiv3.FyersWebsocket import order_ws

def onOrder(message):
    """
    Callback function to handle incoming messages from the FyersDataSocket WebSocket.

    Parameters:
        message (dict): The received message from the WebSocket.

    """
    print("Order Response:", message)

def onerror(message):
    """
    Callback function to handle WebSocket errors.

    Parameters:
        message (dict): The error message received from the WebSocket.

    """
    print("Error:", message)


def onclose(message):
    """
    Callback function to handle WebSocket connection close events.
    """
    print("Connection closed:", message)


def onopen():
    """
    Callback function to subscribe to data type and symbols upon WebSocket connection.

    """
    # Specify the data type and symbols you want to subscribe to
    data_type = "OnOrders"
    # data_type = "OnTrades"
    # data_type = "OnPositions"
    # data_type = "OnGeneral"
    # data_type = "OnOrders,OnTrades,OnPositions,OnGeneral"

    fyers.subscribe(data_type=data_type)

    # Keep the socket running to receive real-time data
    fyers.keep_running()



# Create a FyersDataSocket instance with the provided parameters
fyers = order_ws.FyersOrderSocket(
    access_token=new_access_token,  # Your access token for authenticating with the Fyers API.
    write_to_file=False,        # A boolean flag indicating whether to write data to a log file or not.
    log_path="",                # The path to the log file if write_to_file is set to True (empty string means current directory).
    on_connect=onopen,          # Callback function to be executed upon successful WebSocket connection.
    on_close=onclose,           # Callback function to be executed when the WebSocket connection is closed.
    on_error=onerror,           # Callback function to handle any WebSocket errors that may occur.
    on_orders=onOrder,          # Callback function to handle order-related events from the WebSocket.
)


# Establish a connection to the Fyers WebSocket
fyers.connect()


# ------------------------------------------------------------------------------------------------------------------------------------------
# Sample Success Response 
# ------------------------------------------------------------------------------------------------------------------------------------------
                      
# {
#   "s":"ok",
#   "orders":{
#       "clientId":"XV20986",
#       "id":"23080400089344",
#       "exchOrdId":"1100000009596016",
#       "qty":1,
#       "filledQty":1,
#       "limitPrice":7.95,
#       "type":2,
#       "fyToken":"101000000014366",
#       "exchange":10,
#       "segment":10,
#       "symbol":"NSE:IDEA-EQ",
#       "instrument":0,
#       "offlineOrder":false,
#       "orderDateTime":"04-Aug-2023 10:12:58",
#       "orderValidity":"DAY",
#       "productType":"INTRADAY",
#       "side":-1,
#       "status":90,
#       "source":"W",
#       "ex_sym":"IDEA",
#       "description":"VODAFONE IDEA LIMITED",
#       "orderNumStatus":"23080400089344:2"
#   }
# }




# Order Response: {'s': 'ok', 'orders': 
#                  {'clientId': 'XS45474', 
#                   'id': '24101700487654', 
#                   'qty': 1, 'remainingQuantity': 1, 
#                   'type': 2, 
#                   'fyToken': '1120241205426467', 
#                   'exchange': 11, 
#                   'segment': 20, 
#                   'symbol': 'MCX:SILVER24DECFUT', 
#                   'instrument': 30, 
#                   'offlineOrder': False, 
#                   'orderDateTime': '17-Oct-2024 19:06:19', 
#                   'orderValidity': 'DAY', 
#                   'productType': 'INTRADAY', 
#                   'side': 1, 
#                   'status': 4, 
#                   'source': 'W', 
#                   'ex_sym': 'SILVER', 
#                   'description': 'SILVER 24 Dec 05 FUT',
#                     'orderTag': '2:Untagged', 
#                     'orderNumStatus': '24101700487654:4'}}

# Order Response: {'s': 'ok', 'orders': {
#     'clientId': 'XS45474', 
#     'id': '24101700487654', 
#     'qty': 1, 'remainingQuantity': 0, 'type': 2, 'fyToken': '1120241205426467', 'exchange': 11, 'segment': 20, 'symbol': 'MCX:SILVER24DECFUT', 'instrument': 30, 
#     'message': 'RED:Margin Shortfall:INR 5,25,690.20 Available:INR 0.00 for C-XS45474 [FYERS_RISK_CUG]', 
#     'offlineOrder': False, 'orderDateTime': '17-Oct-2024 19:06:19', 'orderValidity': 'DAY', 'productType': 'INTRADAY', 'side': 1, 
    
#     'status': 5, 'source': 'W', 'ex_sym': 'SILVER', 'description': 'SILVER 24 Dec 05 FUT', 'orderTag': '2:Untagged', 'orderNumStatus': '24101700487654:5'}}







def onTrade(message):
    """
    Callback function to handle incoming messages from the FyersDataSocket WebSocket.

    Parameters:
        message (dict): The received message from the WebSocket.

    """
    print("Trade Response:", message)

def onOrder(message):
    """
    Callback function to handle incoming messages from the FyersDataSocket WebSocket.

    Parameters:
        message (dict): The received message from the WebSocket.

    """
    print("Order Response:", message)

def onPosition(message):
    """
    Callback function to handle incoming messages from the FyersDataSocket WebSocket.

    Parameters:
        message (dict): The received message from the WebSocket.

    """
    print("Position Response:", message)

def onGeneral(message):
    """
    Callback function to handle incoming messages from the FyersDataSocket WebSocket.

    Parameters:
        message (dict): The received message from the WebSocket.

    """
    print("General Response:", message)

def onerror(message):
    """
    Callback function to handle WebSocket errors.

    Parameters:
        message (dict): The error message received from the WebSocket.


    """
    print("Error:", message)


def onclose(message):
    """
    Callback function to handle WebSocket connection close events.
    """
    print("Connection closed:", message)


def onopen():
    """
    Callback function to subscribe to data type and symbols upon WebSocket connection.

    """
    # Specify the data type and symbols you want to subscribe to
    # data_type = "OnOrders"
    # data_type = "OnTrades"
    # data_type = "OnPositions"
    # data_type = "OnGeneral"
    data_type = "OnOrders,OnTrades,OnPositions,OnGeneral"

    fyers.subscribe(data_type=data_type)

    # Keep the socket running to receive real-time data
    fyers.keep_running()



# Create a FyersDataSocket instance with the provided parameters
fyers = order_ws.FyersOrderSocket(
    access_token=new_access_token,  # Your access token for authenticating with the Fyers API.
    write_to_file=False,        # A boolean flag indicating whether to write data to a log file or not.
    log_path="",                # The path to the log file if write_to_file is set to True (empty string means current directory).
    on_connect=onopen,          # Callback function to be executed upon successful WebSocket connection.
    on_close=onclose,           # Callback function to be executed when the WebSocket connection is closed.
    on_error=onerror,           # Callback function to handle any WebSocket errors that may occur.
    on_general=onGeneral,       # Callback function to handle general events from the WebSocket.
    on_orders=onOrder,          # Callback function to handle order-related events from the WebSocket.
    on_positions=onPosition,    # Callback function to handle position-related events from the WebSocket.
    on_trades=onTrade           # Callback function to handle trade-related events from the WebSocket.
)

# Establish a connection to the Fyers WebSocket
fyers.connect()

# ------------------------------------------------------------------------------------------------------------------------------------------
# Sample Success Response 
# ------------------------------------------------------------------------------------------------------------------------------------------
          
#   {
#     "s":"ok",
#     "orders":{
#         "clientId":"XV20986",
#         "id":"23080400089344",
#         "exchOrdId":"1100000009596016",
#         "qty":1,
#         "filledQty":1,
#         "limitPrice":7.95,
#         "type":2,
#         "fyToken":"101000000014366",
#         "exchange":10,
#         "segment":10,
#         "symbol":"NSE:IDEA-EQ",
#         "instrument":0,
#         "offlineOrder":false,
#         "orderDateTime":"04-Aug-2023 10:12:58",
#         "orderValidity":"DAY",
#         "productType":"INTRADAY",
#         "side":-1,
#         "status":90,
#         "source":"W",
#         "ex_sym":"IDEA",
#         "description":"VODAFONE IDEA LIMITED",
#         "orderNumStatus":"23080400089344:2"
#     }
#   }
