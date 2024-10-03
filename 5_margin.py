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
import requests


# Initialize the FyersModel instance with your client_id, access_token, and enable async mode
fyers = fyersModel.FyersModel(client_id=client_id, token=access_token,is_async=False, log_path="")

call_option='NSE:BANKNIFTY24O0951800CE'
put_option='NSE:BANKNIFTY24O0951800PE'
# call_option='MCX:GOLD24NOV75000CE'
# put_option='MCX:GOLD24NOV75000PE'

def get_span_margin(api_key, api_secret):
    url = "https://api.fyers.in/api/v2/span_margin"
    
    headers = {
        'Authorization': f'{api_key}:{access_token}',
        'Content-Type': 'application/json'
    }
    
    data = {
        "data": [

            {
                "symbol": call_option,
                "qty": 15,
                "side": -1,
                "type": 2,
                "productType": "INTRADAY",
                "limitPrice": 0.0,
                "stopLoss": 0.0
            }
            ,
                        {
                "symbol": put_option,
                "qty": 15,
                "side": -1,
                "type": 2,
                "productType": "INTRADAY",
                "limitPrice": 0.0,
                "stopLoss": 0.0
            }
        ]
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        return response.json()
    else:
        return f"Error: {response.status_code}, {response.text}"



result = get_span_margin(client_id, secret_key)
print(result)
# call_price=list(result['individual_info'].values())[0]['total']
# put_price=list(result['individual_info'].values())[1]['total']
# print(result['data']['total'])
# print(call_price,put_price)
# print(call_price+put_price)