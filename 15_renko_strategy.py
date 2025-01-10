# Renko & ema Trading Strategy for Nifty 50

# 1. Strategy Overview
# Renko Box Size:
# a. Calculated using the ATR (14) of the previous day’s 5-minute candles.
# b. Box sizes are rounded to the nearest 10 paisa for each stock.
# Indicators Used:
# a.Renko Charts for price filtering.
# b.ema, applied to Renko closing prices instead of candlestick data.
# Trading Hours:
# The algorithm begins scanning for trades at 9:20 AM to allow for initial market stabilization.
# Uses the first 5-minute candle (from 9:15-9:20 AM) for calculations.
# Profit/Loss Tracking: The algorithm maintains a separate P&L tracker for each stock to monitor individual stock performance. Trades for a specific stock are stopped once the profit or loss for that stock reaches ₹1,000 for the day.
# 2. Entry Rules
# Buy: when renko close greater than ema.
# Sell: When renko close less than ema.
# This ema needs to take the closing price of Renko box and not candles
# 3. Exit Rules
# Stop Loss (SL): 2 Renko bricks (e.g., if the box size is ₹1.5, SL = ₹3).
# Take Profit (TP): Square off 50% of the position at 2 Renko bricks profit. Trail the remaining position until a Renko box reversal (opposite direction brick forms).
# Trade Limits: Maximum 2 trades per stock per day. Stop trading a stock if the profit or loss reaches ₹1,000 for the day. (This is to be tracked only after closing the position)




from fyers_apiv3 import fyersModel
from fyers_apiv3.FyersWebsocket import data_ws
from fyers_apiv3.FyersWebsocket import order_ws
import pandas as pd
import datetime as dt
import pandas_ta as ta

import numpy as np
import asyncio
import pytz
import pickle
import time

import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend
import matplotlib.pyplot as plt
import mplfinance as mpf

#aJ*ch*5-4?4?*?H&l2S&-HYUJciTa%GJ
client_id = '65L1HFF7DC-100'
secret_key = 'DKRVMFUG3U'
redirect_uri ='https://fessorpro.com/'  
with open('access.txt') as f:
    access_token=f.read()


# import os
# import certifi

# os.environ['SSL_CERT_FILE'] = certifi.where()
# print(certifi.where())

st_name='renko_strategy'
import logging
logging.basicConfig(level=logging.INFO, filename=f'{st_name}_{dt.date.today()}.log',filemode='a',format="%(asctime)s - %(message)s")

atr_length=14
sl_brick=2
tp_brick=2
per_stock_money=10000
max_loss_per_stock=1000




account_type='PAPER'

start_hour,start_min=9,35
end_hour,end_min=15,15





ct=dt.datetime.now()
start_time=dt.datetime(ct.year,ct.month,ct.day,start_hour,start_min)
end_time=dt.datetime(ct.year,ct.month,ct.day,end_hour,end_min)

fyers = fyersModel.FyersModel(client_id=client_id, is_async=False, token=access_token, log_path="")
fyers_asysc = fyersModel.FyersModel(client_id=client_id, is_async=True, token=access_token, log_path="")



symbols=['HDFCBANK','RELIANCE','KOTAKBANK','TCS','HCLTECH','WIPRO','TECHM','ICICIBANK','AXISBANK','SBIN']
print(symbols)

exchange='NSE'
sec_type='EQ'

list_of_tickers={}

for t in symbols:
    ticker=f"{exchange}:{t}-{sec_type}"
    list_of_tickers.update({t:ticker})

print(list_of_tickers)
symbols=list(list_of_tickers.values())
df=pd.DataFrame(columns=['name','ltp','ch','chp','avg_trade_price','open_price','high_price','low_price','prev_close_price','vol_traded_today','oi','pdoi','oipercent','bid_price','ask_price','last_traded_time','exch_feed_time','bid_size','ask_size','last_traded_qty','tot_buy_qty','tot_sell_qty','lower_ckt','upper_ckt','type','symbol','expiry' ])
df['name']=symbols
df.set_index('name',inplace=True)

print(df)
print(symbols)


def candle_renko_refresh(ticker):
    print('candle_renko_refresh')
    global paper_option_data_info
    brick_size=paper_option_data_info.get(ticker).get('brick_size')
    # brick_size=3
    data=fetchOHLC(ticker,'1',2)          
    calculated_values = {}
    mpf.plot(data, type='renko', renko_params=dict(brick_size=brick_size),return_calculated_values=calculated_values,returnfig=True,style='yahoo')
    plt.close()
    renko_df = pd.DataFrame(calculated_values)
    last=renko_df['renko_bricks'].iloc[-1]
    def count_bricks(sign_list):
        list1=[]
        pos_count=0
        neg_count=0
        for k in range(len(sign_list)):
            i=sign_list[k]
            if i>0:
                if sign_list[k-1]<0:
                    pos_count=1
                    list1.append(pos_count)
                else:
                    pos_count+=1
                    list1.append(pos_count)

            elif i<0:
                if sign_list[k-1]>0:
                    neg_count=-1
                    list1.append(neg_count)
                else:
                    neg_count-=1
                    list1.append(neg_count)
            else:
                list1.append(0)
        return list1

    renko_df['pos_count']=count_bricks(renko_df['renko_bricks'].diff().tolist())
    renko_df['ema']=ta.ema(renko_df['renko_bricks'],length=8)
    renko_df['trend']=np.where(renko_df['ema']>renko_df['renko_bricks'],'downtrend','uptrend')

    # print(renko_df[["renko_dates",'renko_bricks','pos_count','ema','trend']].tail(20))
    n_brick=renko_df['pos_count'].iloc[-1]

    paper_option_data_info.get(ticker).update({'brick_no':n_brick,'brick_last':last,'renko_df':renko_df})


#getting current position
def get_position():
    position_response=fyers.positions()  ## This will provide all the position related information
    # print(position_response)
    if position_response['netPositions']:
        position_df=pd.DataFrame(position_response['netPositions'])
    else:
        position_df=pd.DataFrame()
    return position_df

#getiting current order
def get_order():
    order_response=fyers.orderbook()  ## This will provide all the order related information
    # print(order_response)
    if order_response['orderBook']:
        order_df=pd.DataFrame(order_response['orderBook'])
    else:
        order_df=pd.DataFrame()
    return order_df


position_df=get_position()
order_df=get_order()    

print(position_df)
print(order_df)


def store(data,account_type):
    pickle.dump(data,open(f'data-{dt.date.today()}-{account_type}.pickle','wb'))

def load(account_type):
    return pickle.load(open(f'data-{dt.date.today()}-{account_type}.pickle', 'rb'))

def fetchOHLC(ticker,interval,duration):
    """extracts historical data and outputs in the form of dataframe"""
    instrument = ticker
    data = {"symbol":instrument,"resolution":interval,"date_format":"1","range_from":dt.date.today()-dt.timedelta(duration),"range_to":dt.date.today(),"cont_flag":"1",'oi_flag':"1"}
    sdata=fyers.history(data)
    # print(sdata)
    sdata=pd.DataFrame(sdata['candles'])
    sdata.columns=['date','open','high','low','close','volume']
    sdata['date']=pd.to_datetime(sdata['date'], unit='s')
    sdata.date=(sdata.date.dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata'))
    sdata['date'] = sdata['date'].dt.tz_localize(None)
    sdata=sdata.set_index('date')
    sdata['atr']=ta.atr(sdata['high'],sdata['low'],sdata['close'],length=atr_length)

    # sdata=sdata.reset_index()[sdata.reset_index()['date'].dt.date<dt.datetime.now().date()].set_index('date')
    # print(sdata)
    return sdata



if account_type=='PAPER':
    try:
        paper_option_data_info=load(account_type)
    except:
        column_names = ['time','ticker','price','action','stop_price','take_profit','quantity']
        filled_df = pd.DataFrame(columns=column_names)
        filled_df.set_index('time',inplace=True)
        paper_option_data_info={}
        for ticker in list_of_tickers.values():
            
            sdata1=fetchOHLC(ticker,'5',3)
            sdata=sdata1.copy()
    
            sdata=sdata.reset_index()[sdata.reset_index()['date'].dt.date<dt.datetime.now().date()].set_index('date')
            atr=round(sdata['atr'].iloc[-1],2)
            # atr=2
            last_price=sdata['close'].iloc[-1]
            initial_quantity=int(per_stock_money/last_price)
            #change quantity to multiple of 2
            initial_quantity=initial_quantity-initial_quantity%2
            paper_option_data_info.update({ticker:{'trade_flag':0,'entry_price':0,'stop_price':0,'profit_price':0,'initial_quantity':initial_quantity,'current_quantity':0,'stop_price':0,"pnl":0,'position':0,'brick_size' : atr,'brick_no':0,'brick_last':0,'renko_df':0,'no_of_trades':0}})
            candle_renko_refresh(ticker)
        paper_option_data_info.update({'filled_df':filled_df})

else:
    try:
        real_option_data_info=load(account_type)
    except:
        column_names = ['time','ticker','price','action','stop_price','take_profit','quantity']
        filled_df = pd.DataFrame(columns=column_names)
        filled_df.set_index('time',inplace=True)
        real_option_data_info={}
        for ticker in list_of_tickers.values():
            
            sdata1=fetchOHLC(ticker,'5',3)
            sdata=sdata1.copy()
    
            sdata=sdata.reset_index()[sdata.reset_index()['date'].dt.date<dt.datetime.now().date()].set_index('date')
            atr=round(sdata['atr'].iloc[-1],2)
            atr=2
            last_price=sdata['close'].iloc[-1]
            initial_quantity=int(per_stock_money/last_price)
            #change quantity to multiple of 2
            initial_quantity=initial_quantity-initial_quantity%2
            real_option_data_info.update({ticker:{'trade_flag':0,'entry_price':0,'stop_price':0,'profit_price':0,'initial_quantity':initial_quantity,'current_quantity':0,'stop_price':0,"pnl":0,'position':0,'brick_size' : atr,'brick_no':0,'brick_last':0,'renko_df':0,'no_of_trades':0}})
            candle_renko_refresh(ticker)
        real_option_data_info.update({'filled_df':filled_df})

def take_position(ticker,action,quantity):

    data = {
                "symbol":ticker,
                "qty":quantity,
                "type":2,
                "side":action,
                "productType":"INTRADAY",
                "limitPrice":0,
                "stopPrice":0,
                "validity":"DAY",
                "disclosedQty":0,
                "offlineOrder":False,
                "stopLoss":0,
                "takeProfit":0
            }

    response3 = fyers.place_order(data=data) #place market buy order
    logging.info(response3)
    print(response3)



def paper_order():
    global paper_option_data_info

    if dt.datetime.now().time()>start_time.time():

        for ticker in list_of_tickers.values():
            last_price=df.loc[ticker,'ltp']
            # print(f"{ticker} last price ={last_price}")

            renko_df=paper_option_data_info.get(ticker).get('renko_df')
            trade_flag=paper_option_data_info.get(ticker).get('trade_flag')
            brick_size=paper_option_data_info.get(ticker).get('brick_size')
            current_quantity=paper_option_data_info.get(ticker).get('current_quantity')
            initial_quantity=paper_option_data_info.get(ticker).get('initial_quantity')
            stop_price=paper_option_data_info.get(ticker).get('stop_price')
            entry_price=paper_option_data_info.get(ticker).get('entry_price')
            no_of_trades=paper_option_data_info.get(ticker).get('no_of_trades')
            # print(renko_df.tail(2))
            
            #end time condition
            if dt.datetime.now().time()>end_time.time():
                if trade_flag==1:
                    #close position
                    
                    paper_option_data_info.get(ticker).update({'trade_flag':2,'current_quantity':0})
                    a=[ticker,last_price,'SELL',0,0,0]
                    paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                    logging.info(f"closing position due to end time for {ticker} at price {last_price}")
                elif trade_flag==-1:
                    #close position
                    paper_option_data_info.get(ticker).update({'trade_flag':-2,'current_quantity':0})
                    a=[ticker,last_price,'BUY',0,0,0]
                    paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                    logging.info(f"closing position due to end time for {ticker} at price {last_price}")
                continue

            #update pnl
            if trade_flag!=0 and not np.isnan(last_price):
                if trade_flag==1:
                    pnl=int((last_price-entry_price)*current_quantity)
                    paper_option_data_info.get(ticker).update({'pnl':pnl})
                    print(f"{ticker} last price {last_price} buy price {entry_price} stop price ={stop_price} pnl ={pnl}")
                    #close position if pnl is greater than max_loss_per_stock
                    if pnl>max_loss_per_stock:
                        paper_option_data_info.get(ticker).update({'trade_flag':2,'current_quantity':0})
                        a=[ticker,last_price,'SELL',0,0,0]
                        paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                        logging.info(f"max loss hit for {ticker} at price {last_price}")
                    
                elif trade_flag==-1:
                    pnl=int((entry_price-last_price)*current_quantity)
                    paper_option_data_info.get(ticker).update({'pnl':pnl})
                    print(f"{ticker} last price {last_price} sell price {entry_price} stop price ={stop_price} pnl ={pnl}")
                    #close position if pnl is greater than max_loss_per_stock
                    if pnl>max_loss_per_stock:
                        paper_option_data_info.get(ticker).update({'trade_flag':-2,'current_quantity':0})
                        a=[ticker,last_price,'BUY',0,0,0]
                        paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                        logging.info(f"max loss hit for {ticker} at price {last_price}")

            #entry
            if (renko_df['trend'].iloc[-1]=='uptrend' and renko_df['trend'].iloc[-2]=='downtrend') and (trade_flag==0) and (no_of_trades<2) :
                no_of_trades+=1
                paper_option_data_info.get(ticker).update({'trade_flag':1,'entry_price':last_price,'stop_price':last_price-(sl_brick*brick_size),'profit_price':last_price+(tp_brick*brick_size),'current_quantity':initial_quantity,'no_of_trades':no_of_trades})
                a=[ticker,last_price,'BUY',last_price-(sl_brick*brick_size),last_price+(tp_brick*brick_size),initial_quantity]
                paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                print('buy condition satisfied')
                logging.info(f"buy condition satisfied for {ticker} at price {last_price}")    

            #trail
            elif trade_flag==1  and (last_price>paper_option_data_info.get(ticker).get('profit_price')):
                if current_quantity==initial_quantity:
                    #close hlaf of our position
                    new_stop_price=last_price-(sl_brick*brick_size)
                    paper_option_data_info.get(ticker).update({'current_quantity':initial_quantity/2,'stop_price':new_stop_price})
                    a=[ticker,last_price,'SELL',new_stop_price,0,initial_quantity/2]
                    paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                    logging.info(f"half position closed for {ticker} at price {last_price}")

                
                elif current_quantity!=initial_quantity:
                    #change stop price
                    if last_price-(brick_size*sl_brick)>stop_price+(brick_size):
                        new_stop_price=last_price-(sl_brick*brick_size)
                        logging.info(f'updating stop price , current_stop is {stop_price} new stop is {new_stop_price} current price is {last_price}')
                        paper_option_data_info.get(ticker).update({'stop_price':new_stop_price})
                        # a=[ticker,last_price,'TRAIL',new_stop_price,0,current_quantity]
                        # paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                        logging.info(f"trailing stop loss for {ticker} at price {last_price}")

            #exit
            elif trade_flag==1 and  (last_price<paper_option_data_info.get(ticker).get('stop_price')):
                #close position
                paper_option_data_info.get(ticker).update({'trade_flag':0,'current_quantity':0})
                a=[ticker,last_price,'SELL',0,0,0]
                paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                logging.info(f"stop loss hit for {ticker} at price {last_price}")

            #entry
            if (renko_df['trend'].iloc[-1]=='downtrend' and renko_df['trend'].iloc[-2]=='uptrend') and (trade_flag==0) and (no_of_trades<2 ):
                no_of_trades+=1
                paper_option_data_info.get(ticker).update({'trade_flag':-1,'entry_price':last_price,'stop_price':last_price+(sl_brick*brick_size),'profit_price':last_price-(tp_brick*brick_size),'current_quantity':initial_quantity,'no_of_trades':no_of_trades})
                a=[ticker,last_price,'SELL',last_price+(sl_brick*brick_size),last_price-(tp_brick*brick_size),initial_quantity]
                paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                print('sell condition satisfied')
                logging.info(f"sell condition satisfied for {ticker} at price {last_price}")

            #trail      
            elif trade_flag==-1  and (last_price<paper_option_data_info.get(ticker).get('profit_price')):

                if current_quantity==initial_quantity:
                    new_stop_price=last_price+(sl_brick*brick_size)
                    paper_option_data_info.get(ticker).update({'current_quantity':initial_quantity/2,'stop_price':new_stop_price})
                    a=[ticker,last_price,'BUY',new_stop_price,0,initial_quantity/2]
                    paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                    logging.info(f"half position closed for {ticker} at price {last_price}")
                
                elif current_quantity!=initial_quantity:
                    #change stop price
                    if last_price+(brick_size*sl_brick)<stop_price-(brick_size):
                        new_stop_price=last_price+(sl_brick*brick_size)
                        logging.info(f'updating stop price , current_stop is {stop_price} new stop is {new_stop_price} current price is {last_price}')
                        paper_option_data_info.get(ticker).update({'stop_price':new_stop_price})
                        # a=[ticker,last_price,'TRAIL',new_stop_price,0,current_quantity]
                        # paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                        logging.info(f"trailing stop loss for {ticker} at price {last_price}")

            #exit    
            elif trade_flag==-1 and  (last_price>paper_option_data_info.get(ticker).get('stop_price')):
                #close position
                paper_option_data_info.get(ticker).update({'trade_flag':0,'current_quantity':0})
                a=[ticker,last_price,'BUY',0,0,0]
                paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                logging.info(f"stop loss hit for {ticker} at price {last_price}")

            
            if not paper_option_data_info['filled_df'].empty:
                paper_option_data_info['filled_df'].to_csv(f'{st_name}_trades_{dt.date.today()}.csv')
            
        store(paper_option_data_info,account_type)
            

def real_order():
    global real_option_data_info

    if dt.datetime.now().time()>start_time.time():

        for ticker in list_of_tickers.values():
            last_price=df.loc[ticker,'ltp']
            # print(f"{ticker} last price ={last_price}")

            renko_df=real_option_data_info.get(ticker).get('renko_df')
            trade_flag=real_option_data_info.get(ticker).get('trade_flag')
            brick_size=real_option_data_info.get(ticker).get('brick_size')
            current_quantity=real_option_data_info.get(ticker).get('current_quantity')
            initial_quantity=real_option_data_info.get(ticker).get('initial_quantity')
            stop_price=real_option_data_info.get(ticker).get('stop_price')
            entry_price=real_option_data_info.get(ticker).get('entry_price')
            no_of_trades=real_option_data_info.get(ticker).get('no_of_trades')
            # print(renko_df.tail(2))
            
            #end time condition
            if dt.datetime.now().time()>end_time.time():
                if trade_flag==1:
                    #close position
                    
                    real_option_data_info.get(ticker).update({'trade_flag':2,'current_quantity':0})
                    a=[ticker,last_price,'SELL',0,0,0]
                    real_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                    logging.info(f"closing position due to end time for {ticker} at price {last_price}")
                    data = {"id":ticker+"-INTRADAY"}
                    response = fyers.exit_positions(data=data)
                    logging.info(response)


                elif trade_flag==-1:
                    #close position
                    real_option_data_info.get(ticker).update({'trade_flag':-2,'current_quantity':0})
                    a=[ticker,last_price,'BUY',0,0,0]
                    real_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                    logging.info(f"closing position due to end time for {ticker} at price {last_price}")
                    data = {"id":ticker+"-INTRADAY"}
                    response = fyers.exit_positions(data=data)
                    logging.info(response)

                continue

            #update pnl
            if trade_flag!=0 and not np.isnan(last_price):
                if trade_flag==1:
                    pnl=int((last_price-entry_price)*current_quantity)
                    real_option_data_info.get(ticker).update({'pnl':pnl})
                    print(f"{ticker} last price {last_price} buy price {entry_price} stop price ={stop_price} pnl ={pnl}")
                    #close position if pnl is greater than max_loss_per_stock
                    if pnl>max_loss_per_stock:
                        real_option_data_info.get(ticker).update({'trade_flag':2,'current_quantity':0})
                        a=[ticker,last_price,'SELL',0,0,0]
                        real_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                        logging.info(f"max loss hit for {ticker} at price {last_price}")
                        data = {"id":ticker+"-INTRADAY"}
                        response = fyers.exit_positions(data=data)
                        logging.info(response)
                elif trade_flag==-1:
                    pnl=int((entry_price-last_price)*current_quantity)
                    real_option_data_info.get(ticker).update({'pnl':pnl})
                    print(f"{ticker} last price {last_price} sell price {entry_price} stop price ={stop_price} pnl ={pnl}")
                    #close position if pnl is greater than max_loss_per_stock
                    if pnl>max_loss_per_stock:
                        real_option_data_info.get(ticker).update({'trade_flag':-2,'current_quantity':0})
                        a=[ticker,last_price,'BUY',0,0,0]
                        real_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                        logging.info(f"max loss hit for {ticker} at price {last_price}")
                        data = {"id":ticker+"-INTRADAY"}
                        response = fyers.exit_positions(data=data)
                        logging.info(response)
            
            #entry
            if (renko_df['trend'].iloc[-1]=='uptrend' and renko_df['trend'].iloc[-2]=='downtrend') and (trade_flag==0) and (no_of_trades<2) :
                no_of_trades+=1
                real_option_data_info.get(ticker).update({'trade_flag':1,'entry_price':last_price,'stop_price':last_price-(sl_brick*brick_size),'profit_price':last_price+(tp_brick*brick_size),'current_quantity':initial_quantity,'no_of_trades':no_of_trades})
                a=[ticker,last_price,'BUY',last_price-(sl_brick*brick_size),last_price+(tp_brick*brick_size),initial_quantity]
                real_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                
                print('buy condition satisfied')

                logging.info(f"buy condition satisfied for {ticker} at price {last_price}")
                take_position(ticker,1,initial_quantity)
            
            #trail
            elif trade_flag==1  and (last_price>real_option_data_info.get(ticker).get('profit_price')):
                if current_quantity==initial_quantity:
                    new_stop_price=last_price-(sl_brick*brick_size)
                    real_option_data_info.get(ticker).update({'current_quantity':initial_quantity/2,'stop_price':new_stop_price})
                    a=[ticker,last_price,'SELL',new_stop_price,0,initial_quantity/2]
                    real_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                    logging.info(f"half position closed for {ticker} at price {last_price}")

                
                elif current_quantity!=initial_quantity:
                    #change stop price
                    if last_price-(brick_size*sl_brick)>stop_price+(brick_size):
                        new_stop_price=last_price-(sl_brick*brick_size)
                        logging.info(f'updating stop price , current_stop is {stop_price} new stop is {new_stop_price} current price is {last_price}')
                        real_option_data_info.get(ticker).update({'stop_price':new_stop_price})
                        # a=[ticker,last_price,'TRAIL',new_stop_price,0,current_quantity]
                        # real_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                        logging.info(f"trailing stop loss for {ticker} at price {last_price}")
            
            #exit
            elif trade_flag==1 and  (last_price<real_option_data_info.get(ticker).get('stop_price')):
                #close position
                real_option_data_info.get(ticker).update({'trade_flag':0,'current_quantity':0})
                a=[ticker,last_price,'SELL',0,0,0]
                real_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                logging.info(f"stop loss hit for {ticker} at price {last_price}")
                data = {"id":ticker+"-INTRADAY"}
                response = fyers.exit_positions(data=data)
                logging.info(response)
            
            #entry
            if (renko_df['trend'].iloc[-1]=='downtrend' and renko_df['trend'].iloc[-2]=='uptrend') and (trade_flag==0) and (no_of_trades<2 ):
                no_of_trades+=1
                real_option_data_info.get(ticker).update({'trade_flag':-1,'entry_price':last_price,'stop_price':last_price+(sl_brick*brick_size),'profit_price':last_price-(tp_brick*brick_size),'current_quantity':initial_quantity,'no_of_trades':no_of_trades})
                a=[ticker,last_price,'SELL',last_price+(sl_brick*brick_size),last_price-(tp_brick*brick_size),initial_quantity]
                real_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                
                print('sell condition satisfied')
                logging.info(f"sell condition satisfied for {ticker} at price {last_price}")
                take_position(ticker,-1,initial_quantity)
                
            
            #trail
            elif trade_flag==-1  and (last_price<real_option_data_info.get(ticker).get('profit_price')):
                if current_quantity==initial_quantity:
                    new_stop_price=last_price+(sl_brick*brick_size)
                    real_option_data_info.get(ticker).update({'current_quantity':initial_quantity/2,'stop_price':new_stop_price})
                    a=[ticker,last_price,'BUY',new_stop_price,0,initial_quantity/2]
                    real_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                    logging.info(f"half position closed for {ticker} at price {last_price}")

                
                elif current_quantity!=initial_quantity:
                    #change stop price
                    if last_price+(brick_size*sl_brick)<stop_price-(brick_size):
                        new_stop_price=last_price+(sl_brick*brick_size)
                        logging.info(f'updating stop price , current_stop is {stop_price} new stop is {new_stop_price} current price is {last_price}')
                        real_option_data_info.get(ticker).update({'stop_price':new_stop_price})
                        # a=[ticker,last_price,'TRAIL',new_stop_price,0,current_quantity]
                        # real_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                        logging.info(f"trailing stop loss for {ticker} at price {last_price}")
            
            #exit
            elif trade_flag==-1 and  (last_price>real_option_data_info.get(ticker).get('stop_price')):
                #close position
                real_option_data_info.get(ticker).update({'trade_flag':0,'current_quantity':0})
                a=[ticker,last_price,'BUY',0,0,0]
                real_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                logging.info(f"stop loss hit for {ticker} at price {last_price}")
                data = {"id":ticker+"-INTRADAY"}
                response = fyers.exit_positions(data=data)
                logging.info(response)
            
            if not real_option_data_info['filled_df'].empty:
                real_option_data_info['filled_df'].to_csv(f'{st_name}_trades_{dt.date.today()}.csv')
        
        store(real_option_data_info,account_type)



def onmessage(ticks):
    global df
    # print(ticks)
    if ticks.get('symbol'):
        for key,value in ticks.items():
            #updating dataframe
            df.loc[ticks.get('symbol'), key] = value
            df.drop_duplicates(inplace=True)

def onerror(message):
    print("Error:", message)

def onclose(message):
    print("Connection closed:", message)

def onopen():
    global symbols
    # Specify the data type and symbols you want to subscribe to
    data_type = "SymbolUpdate"

    fyers_socket.subscribe(symbols=symbols, data_type=data_type)

    # Keep the socket running to receive real-time data
    fyers_socket.keep_running()
    print('starting socket')
   

# Create a FyersDataSocket instance with the provided parameters
fyers_socket = data_ws.FyersDataSocket(
    access_token=f"{client_id}:{access_token}",  # Access token in the format "appid:accesstoken"
    log_path="",  # Path to save logs. Leave empty to auto-create logs in the current directory.
    litemode=False,  # Lite mode disabled. Set to True if you want a lite response.
    write_to_file=False,  # Save response in a log file instead of printing it.
    reconnect=True,  # Enable auto-reconnection to WebSocket on disconnection.
    on_connect=onopen,  # Callback function to subscribe to data upon connection.
    on_close=onclose,  # Callback function to handle WebSocket connection close events.
    on_error=onerror,  # Callback function to handle WebSocket errors.
    on_message=onmessage  # Callback function to handle incoming messages from the WebSocket.
)

fyers_socket.connect()



time.sleep(3)

async def main_strategy_code():
    global df
    
    while True:
 
        ct=dt.datetime.now()

        if ct.second in range(1,60,3):
            try:
                pos1=fyers.positions()
                pnl=int(pos1.get('overall').get('pl_total'))
            except:
                print('unable to fetch pnl')
            print(pnl)
        
        #every 1 min
        if ct.second == 2:
            for ticker in list_of_tickers.values():
                candle_renko_refresh(ticker)



        if df.shape[0]!=0:
            print(ct)

            if account_type=='PAPER':
                paper_order()
            # else:
            #     real_order()

        await asyncio.sleep(1)

time.sleep(3)
async def main():
    while True:
        await main_strategy_code()

asyncio.run(main())