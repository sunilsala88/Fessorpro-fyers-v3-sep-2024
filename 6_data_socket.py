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

exchange='NSE'
sec_type='INDEX'
symbol='NIFTYBANK'

index_symbol='NSE:NIFTYBANK-INDEX'

ticker1='MCX:SILVER24DECFUT'
ticker2='MCX:GOLD24DECFUT'


from fyers_apiv3.FyersWebsocket import data_ws


def onmessage(message):
    """
    Callback function to handle incoming messages from the FyersDataSocket WebSocket.

    Parameters:
        message (dict): The received message from the WebSocket.

    """
    print("Response:", message)
    # name=message.get('symbol')
    # time=dt.datetime.fromtimestamp(message.get('last_traded_time'))
    # ltp=message.get('ltp')
    # volume=message.get('vol_traded_today')
    # print(name,time,ltp,volume)


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
    data_type = "SymbolUpdate"

    # Subscribe to the specified symbols and data type
    symbols = [index_symbol]
    fyers.subscribe(symbols=symbols, data_type=data_type)

    # Keep the socket running to receive real-time data
    fyers.keep_running()


# Replace the sample access token with your actual access token obtained from Fyers
new_access_token = f"{client_id}:{access_token}"

# Create a FyersDataSocket instance with the provided parameters
fyers = data_ws.FyersDataSocket(
    access_token=new_access_token,       # Access token in the format "appid:accesstoken"
    log_path="",                     # Path to save logs. Leave empty to auto-create logs in the current directory.
    litemode=False,                  # Lite mode disabled. Set to True if you want a lite response.
    write_to_file=False,              # Save response in a log file instead of printing it.
    reconnect=True,                  # Enable auto-reconnection to WebSocket on disconnection.
    on_connect=onopen,               # Callback function to subscribe to data upon connection.
    on_close=onclose,                # Callback function to handle WebSocket connection close events.
    on_error=onerror,                # Callback function to handle WebSocket errors.
    on_message=onmessage             # Callback function to handle incoming messages from the WebSocket.
)

# Establish a connection to the Fyers WebSocket
fyers.connect()

#   ------------------------------------------------------------------------------------------------------------------------------------------
#  Sample Success Response 
#  ------------------------------------------------------------------------------------------------------------------------------------------
           
#   {
#     "ltp":606.4,
#     "vol_traded_today":3045212,
#     "last_traded_time":1690953622,
#     "exch_feed_time":1690953622,
#     "bid_size":2081,
#     "ask_size":903,
#     "bid_price":606.4,
#     "ask_price":606.45,
#     "last_traded_qty":5,
#     "tot_buy_qty":749960,
#     "tot_sell_qty":1092063,
#     "avg_trade_price":608.2,
#     "low_price":605.85,
#     "high_price":610.5,
#     "open_price":609.85,
#     "prev_close_price":620.2,
#     "type":"sf",
#     "symbol":"NSE:SBIN-EQ",
#     "ch":-13.8,
#     "chp":-2.23
#   }


# Response: {'ltp': 91854.0, 
#            'vol_traded_today': 10569, 
#            'last_traded_time': 1729170092, 
#            'exch_feed_time': 1729170095, 
#            'bid_size': 1, 
#            'ask_size': 1, 
#            'bid_price': 91846.0, 
#            'ask_price': 91866.0, 
#            'last_traded_qty': 1, 
#            'tot_buy_qty': 992, 
#            'tot_sell_qty': 968, 
#            'avg_trade_price': 91770.91, 
#            'low_price': 91130.0, 
#            'high_price': 92445.0, 
#            'lower_ckt': 0, 
#            'upper_ckt': 0, 
           
#            'open_price': 91837.0, 
#            'prev_close_price': 92183.0, 
#            'type': 'sf', 
#            'symbol': 'MCX:SILVER24DECFUT', 
#            'ch': -329.0, 
#            'chp': -0.3569}



# Response: {'bid_price1': 92099.0, 
#            'bid_price2': 92084.0, 
#            'bid_price3': 92082.0, 
#            'bid_price4': 92081.0, 
#            'bid_price5': 92080.0, 
#            'ask_price1': 92114.0, 
#            'ask_price2': 92115.0, 
#            'ask_price3': 92116.0, 
#            'ask_price4': 92118.0, 
#            'ask_price5': 92119.0, 
#            'bid_size1': 3, 
#            'bid_size2': 1, 'bid_size3': 1, 'bid_size4': 1, 'bid_size5': 1, 
#            'ask_size1': 1, 'ask_size2': 3, 'ask_size3': 2, 'ask_size4': 1, 'ask_size5': 1, 
#            'bid_order1': 1, 'bid_order2': 1, 'bid_order3': 1, 'bid_order4': 1, 'bid_order5': 1, 
#            'ask_order1': 1, 'ask_order2': 3, 'ask_order3': 2, 'ask_order4': 1, 'ask_order5': 1, 
#            'type': 'dp', 'symbol': 'MCX:SILVER24DECFUT'}
