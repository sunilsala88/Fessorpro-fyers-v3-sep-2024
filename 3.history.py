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

ticker=f"{exchange}:{symbol}-{sec_type}"
print(ticker)

# Initialize the FyersModel instance with your client_id, access_token, and enable async mode
fyers = fyersModel.FyersModel(client_id=client_id, is_async=False, token=access_token, log_path="")

# current_date=dt.date.today()
# data = {
#     "symbol":ticker,
#     "resolution":"1",
#     "date_format":'1',
#     "range_from":(current_date-dt.timedelta(days=30)),
#     "range_to":current_date,
#     "cont_flag":1,

# }

# response = fyers.history(data=data)
# print(response)
# history_df=pd.DataFrame(response['candles'])


# history_df.columns=['date','open','high','low','close','volume']
# history_df['date']=pd.to_datetime(history_df['date'], unit='s')
# history_df.date=(history_df.date.dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata'))
# history_df['date'] = history_df['date'].dt.tz_localize(None)
# history_df=history_df.set_index('date')
# print(history_df)



def fetchOHLC(ticker,interval,duration):
    """extracts historical data and outputs in the form of dataframe"""
    instrument = ticker
    data = {"symbol":instrument,"resolution":interval,"date_format":"1","range_from":dt.date.today()-dt.timedelta(duration),"range_to":dt.date.today(),"cont_flag":"1",'oi_flag':"1"}
    sdata=fyers.history(data)
    # print(sdata)
    sdata=pd.DataFrame(sdata['candles'])
    sdata.columns=['date','open','high','low','close','volume','OI']
    sdata['date']=pd.to_datetime(sdata['date'], unit='s')
    sdata.date=(sdata.date.dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata'))
    sdata['date'] = sdata['date'].dt.tz_localize(None)
    sdata=sdata.set_index('date')
    return sdata


exchange='NSE'
sec_type='INDEX'
symbol='NIFTYBANK'
ticker=f"{exchange}:{symbol}-{sec_type}"
print(ticker)
ticker='MCX:GOLD24OCTFUT'
data=fetchOHLC(ticker,'1',5)
print(data)


def gethistory(symbol1,type,duration):
    symbol="NSE:"+symbol1+"-"+type
    start=dt.date.today()-dt.timedelta(duration)
    end=dt.date.today()-dt.timedelta()
    sdata=pd.DataFrame()
    while start <= end:
        end2=start+dt.timedelta(60)
        data = {"symbol":symbol,"resolution":"1","date_format":"1","range_from":start,"range_to":end2,"cont_flag":"1"}
        s=fyers.history(data)
        s=pd.DataFrame(s['candles'])
        sdata=pd.concat([sdata,s],ignore_index=True)
        start=end2+dt.timedelta(1)
    sdata.columns=['date','open','high','low','close','volume']
    sdata["date"]=pd.to_datetime(sdata['date'], unit='s')
    sdata.date=(sdata.date.dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata'))
    sdata['date'] = sdata['date'].dt.tz_localize(None)
    sdata=sdata.set_index('date')
    return sdata


# data=gethistory('NIFTYBANK','INDEX',3000)
# print(data)



ticker='MCX:GOLD24OCTFUT'

#QUOTE
data = {
    "symbols":ticker
}

response = fyers.quotes(data=data)
print(response)


#OPTION CHAIN

data = {
    "symbol":ticker,
    "strikecount":1,
    "timestamp": ""
}
response = fyers.optionchain(data=data);
print(response)

chain=pd.DataFrame(response['data']['optionsChain'])
print(chain)


#market depth
data = {
    "symbol":ticker,
    "ohlcv_flag":"1"
}

response = fyers.depth(data=data)
print(response)