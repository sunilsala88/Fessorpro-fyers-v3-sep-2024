# Supertrend and EMA Strategy
# Calculate the Supertrend on daily candles.
# Calculate the EMA (Exponential Moving Average) on hourly candles.
# Go Long:When the daily Supertrend gives a long signal and the closing price is greater than the daily EMA.
# Go Short:When the daily Supertrend gives a short signal.The closing price is less than the daily EMA.


import credentials as crs
from fyers_apiv3 import fyersModel
import pandas as pd
import datetime as dt
import pandas_ta as ta
import time
#credentials
# Replace these values with your actual API credentials
client_id = crs.client_id
secret_key = crs.secret_key
redirect_uri = crs.redirect_uri
with open('access.txt') as f:
    access_token=f.read()

list_of_stocks=['RELIANCE','HDFCBANK','ONGC']

exchange='NSE'
sec_type='EQ'

list_of_tickers={}

for t in list_of_stocks:
    ticker=f"{exchange}:{t}-{sec_type}"
    list_of_tickers.update({t:ticker})

print(list_of_tickers)

#timframe is 1 min
time_frame=1
days=20
start_hour,start_min=18,51
end_hour,end_min=19,55

# Initialize the FyersModel instance with your client_id, access_token, and enable async mode
fyers = fyersModel.FyersModel(client_id=client_id, is_async=False, token=access_token, log_path="")


def get_open_position():
    position_response=fyers.positions()  ## This will provide all the position related information
    # print(position_response)
    if position_response['netPositions']:
        position_df=pd.DataFrame(position_response['netPositions'])
    else:
        position_df=pd.DataFrame()
    return position_df

def get_open_orders():
    order_response=fyers.orderbook()  ## This will provide all the order related information
    # print(order_response)
    if order_response['orderBook']:
        order_df=pd.DataFrame(order_response['orderBook'])
    else:
        order_df=pd.DataFrame()
    return order_df


def get_historical_data(ticker,interval,duration):
    """extracts historical data and outputs in the form of dataframe"""
    instrument = ticker
    data = {"symbol":instrument,"resolution":interval,"date_format":"1","range_from":dt.date.today()-dt.timedelta(duration),"range_to":dt.date.today(),"cont_flag":"1"}
    sdata=fyers.history(data)
    # print(sdata)
    sdata=pd.DataFrame(sdata['candles'])
    sdata.columns=['date','open','high','low','close','volume']
    sdata['date']=pd.to_datetime(sdata['date'], unit='s')
    sdata.date=(sdata.date.dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata'))
    sdata['date'] = sdata['date'].dt.tz_localize(None)
    sdata=sdata.set_index('date')
    sdata['supertrend']=ta.sma(sdata['close'],length=10)
    sdata['ema']=ta.ema(sdata.close, length=20)
    sdata['super']=ta.supertrend(sdata.high,sdata.low,sdata.close,length=10)['SUPERTd_10_3.0']
    sdata['atr']=ta.atr(sdata.high, sdata.low, sdata.close, length=14)
    return sdata


def close_all_orders():
    order_df=get_open_orders()
    if not order_df.empty:
        order_df=order_df[(order_df['status']==6) | (order_df['status']==4) | (order_df['status']==3)]
        if not order_df.empty :
            for id in order_df['id'].to_list():
                data = {"id":id}
                response = fyers.cancel_order(data=data)
                print(response)

def check_market_order_placed(ticker):
    order_df=get_open_orders()
    order_df=order_df[order_df['type']==2]
    order_df=order_df[(order_df['status']==6) | (order_df['status']==4) | (order_df['status']==3)]
    print(order_df)
    if not order_df.empty and (ticker in order_df['symbol'].to_list()):
       return 0
    else:
        return 1

def close_ticker_open_orders(ticker):

    order_df=get_open_orders()
    if not order_df.empty:
        order_df=order_df[(order_df['status']==6) | (order_df['status']==4) | (order_df['status']==3)]
        if (not order_df.empty) and (ticker in order_df['symbol'].to_list()):
            id=order_df[order_df['symbol']==ticker]['id'].iloc[0]
            data = {"id":id}
            response = fyers.cancel_order(data=data)
            print(response)
            
        else:
            print('no order to close')


def close_ticker_postion(name):
    position_df=get_open_position()
    if (not position_df.empty) and (name in position_df['symbol'].to_list()):
        id=position_df[position_df['symbol']==name]['id'].iloc[0]
        data = {
            "id":id
        }
        print(data)
        response = fyers.exit_positions(data=data)
        print(response)
        print('position closed')
    else:
        print('position does not exist')
 


def trade_sell_stocks(stock_name,stock_price,stop_price,quantity=1):
   
    if check_market_order_placed(ticker):
        data = {
                    "symbol":stock_name,
                    "qty":quantity,
                    "type":2,
                    "side":-1,
                    "productType":"INTRADAY",
                    "limitPrice":0,
                    "stopPrice":0,
                    "validity":"DAY",
                    "disclosedQty":0,
                    "offlineOrder":False,
                    "stopLoss":0,
                    "takeProfit":0
                }

        response3 = fyers.place_order(data=data)
        if response3['s']=='ok':
            a=[stock_name,stock_price,'SELL',quantity] 
            
            print('call buy condition satisfied')

            data = {
                "symbol":stock_name,
                "qty":quantity,
                "type":3,
                "side":1,
                "productType":"INTRADAY",
                "limitPrice":0,
                "stopPrice":stop_price,
                "validity":"DAY",
                "disclosedQty":0,
                "offlineOrder":False,
                "orderTag":"tag1"
                }
            response3 = fyers.place_order(data=data)
            print(response3)

        else:
            print('order did not go through')
            print(response3)
        #placing stop order


def trade_buy_stocks(stock_name,stock_price,stop_price,quantity=1):
    if check_market_order_placed(ticker):
        data = {
            "symbol":stock_name,
            "qty":quantity,
            "type":2,
            "side":1,
            "productType":"INTRADAY",
            "limitPrice":0,
            "stopPrice":0,
            "validity":"DAY",
            "disclosedQty":0,
            "offlineOrder":False,
            "stopLoss":0,
            "takeProfit":0
        }

        response3 = fyers.place_order(data=data)
        if response3['s']=='ok':
            a=[stock_name,stock_price,'BUY',quantity] 
            print('print done buying')
            print('call buy condition satisfied')

            #placing stop order
            data = {
            "symbol":stock_name,
            "qty":quantity,
            "type":3,
            "side":-1,
            "productType":"INTRADAY",
            "limitPrice":0,
            "stopPrice":stop_price,
            "validity":"DAY",
            "disclosedQty":0,
            "offlineOrder":False,
            "orderTag":"tag1"
            }
            response3 = fyers.place_order(data=data)
            print(response3)

        else:
            print('order did not go through')
            print(response3)


def strategy_condition(hist_df_hourly,hist_df_daily,ticker):
    print('inside strategy conditional code ')
    # print(hist_df)
    print(ticker)
    buy_condition=hist_df_hourly['super'].iloc[-1]>0 and hist_df_daily['ema'].iloc[-1]<hist_df_hourly['close'].iloc[-1]
    # buy_condition=True
    sell_condition=hist_df_hourly['super'].iloc[-1]<0 and hist_df_daily['ema'].iloc[-1]>hist_df_hourly['close'].iloc[-1]
    # sell_condition=True

    money = int(fyers.funds()['fund_limit'][0]['equityAmount'])
    money=money/3
    print(money)
    hourly_closing_price=hist_df_hourly['close'].iloc[-1]
    atr_value=hist_df_daily['atr'].iloc[-1]

    if money>hourly_closing_price:
        if buy_condition:
            print('buy condition satisfied')
            trade_buy_stocks(ticker,hourly_closing_price,hourly_closing_price-atr_value)
        elif sell_condition:
            print('sell condition satisfied')
            trade_sell_stocks(ticker,hourly_closing_price,hourly_closing_price+atr_value)

        else:
            print('no condition satisfied')
    else:
        print('we dont have enough money to trade')




def main_strategy():
    pos_df= get_open_position()
    ord_df= get_open_orders()
    print(pos_df)
    print(ord_df)

    for ticker in list_of_tickers.values():
        print(ticker)
        #historical data with indicator data
        hist_df=get_historical_data(ticker,f'{time_frame}',days)
        # print(hist_df)
        hist_df_hourly=get_historical_data(ticker,'60',10)
        hist_df_daily=get_historical_data(ticker,'D',50)

        money = int(fyers.funds()['fund_limit'][0]['equityAmount'])
        money=money/3
        print(money)
        closing_price=hist_df['close'].iloc[-1]
        print(closing_price)
        quantity=money/closing_price
        print(quantity)

        if quantity<1:
            continue

        if pos_df.empty:
            print('we dont have any position')
            strategy_condition(hist_df,ticker)

        elif len(pos_df)!=0 and ticker not in pos_df['symbol'].to_list():
            print('we have some position but ticker is not in pos')
            strategy_condition(hist_df,ticker)
        

        elif len(pos_df)!=0 and ticker in pos_df['symbol'].to_list():
            print('we have some pos and ticker is in pos')
            curr_quant=float(pos_df[pos_df['symbol']==ticker]['qty'].iloc[-1])
            print(curr_quant)

            if curr_quant==0:
                print('my quantity is 0')
                strategy_condition(hist_df,ticker)

            elif curr_quant>0:

  
                print('we have current ticker in position and is long')
                sell_condition=hist_df_hourly['super'].iloc[-1]<0 and hist_df_daily['ema'].iloc[-1]>hist_df_hourly['close'].iloc[-1]
   
                if sell_condition:
                            hourly_closing_price=hist_df_hourly['close'].iloc[-1]
                            atr_value=hist_df_daily['atr'].iloc[-1]
                            print('sell condition satisfied')
                
                            close_ticker_open_orders(ticker)
                            time.sleep(1)
                            close_ticker_postion(ticker)
                            time.sleep(1)
                            trade_sell_stocks(ticker,hourly_closing_price,hourly_closing_price+atr_value)

            elif curr_quant<0:
                print('we have current ticker in position and is short')

                hourly_closing_price=hist_df_hourly['close'].iloc[-1]
                atr_value=hist_df_daily['atr'].iloc[-1]
                buy_condition=hist_df_hourly['super'].iloc[-1]>0 and hist_df_daily['ema'].iloc[-1]<hist_df_hourly['close'].iloc[-1]

                if buy_condition:
                            print('buy condiiton satisfied')
                 
                            close_ticker_open_orders(ticker)
                            time.sleep(1)
                            close_ticker_postion(ticker)    
                            time.sleep(1)            
                            trade_buy_stocks(ticker,hourly_closing_price,hourly_closing_price-atr_value)
     



current_time=dt.datetime.now()
print(current_time)

start_time=dt.datetime(current_time.year,current_time.month,current_time.day,start_hour,start_min)
end_time=dt.datetime(current_time.year,current_time.month,current_time.day,end_hour,end_min)

print(start_time)
print(end_time)


#pre hour and post hour

while dt.datetime.now()<start_time :
    print(dt.datetime.now())
    time.sleep(1)

print('we have reached start time ')
print('we are running our strategy now')


while True:
    if dt.datetime.now()>end_time:
        break
    ct=dt.datetime.now()
    print(ct)
    if ct.second in range(1,3) and ct.minute in range(0,60,time_frame):
        main_strategy()
    time.sleep(1)



print('we have reached end time')


response = fyers.exit_positions(data={})
print(response)
#closing all orders
close_all_orders()