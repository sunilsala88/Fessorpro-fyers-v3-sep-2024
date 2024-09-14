import credentials as crs
from fyers_apiv3 import fyersModel
import pandas as pd
#credentials
# Replace these values with your actual API credentials
client_id = crs.client_id
secret_key = crs.secret_key
redirect_uri = crs.redirect_uri
with open('access.txt') as f:
    access_token=f.read()



# Initialize the FyersModel instance with your client_id, access_token, and enable async mode
fyers = fyersModel.FyersModel(client_id=client_id, token=access_token,is_async=False, log_path="")

# Make a request to get the funds information
response = fyers.funds()


data=response.get('fund_limit')
df=pd.DataFrame(data)
print(df)


#order book

order_response=fyers.orderbook()  ## This will provide all the order related information
# print(order_response)
if order_response['orderBook']:
    order_df=pd.DataFrame(order_response['orderBook'])
else:
    order_df=pd.DataFrame()
print(order_df)

#position

position_response=fyers.positions()  ## This will provide all the position related information
# print(position_response)
if position_response['netPositions']:
    position_df=pd.DataFrame(position_response['netPositions'])
else:
    position_df=pd.DataFrame()
print(position_df)

#trade book
trade_response=fyers.tradebook()  ## This will provide all the trade related information 
#convert to dataframe if response has data otherwise empty dataframe
# print(trade_response)
if trade_response['tradeBook']:
    trade_df=pd.DataFrame(trade_response['tradeBook'])
else:
    trade_df=pd.DataFrame()
print(trade_df)
