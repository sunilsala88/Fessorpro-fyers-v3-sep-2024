import credentials as crs
from fyers_apiv3 import fyersModel
import pandas as pd
import datetime as dt
import numpy as np
import pandas_ta as ta
import math
#credentials
# Replace these values with your actual API credentials
client_id = crs.client_id
secret_key = crs.secret_key
redirect_uri = crs.redirect_uri
with open('access.txt') as f:
    access_token=f.read()

exchange='NSE'
sec_type='INDEX'
symbol='NIFTY50'

ticker=f"{exchange}:{symbol}-{sec_type}"
print(ticker)

# Initialize the FyersModel instance with your client_id, access_token, and enable async mode
fyers = fyersModel.FyersModel(client_id=client_id, is_async=False, token=access_token, log_path="")


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
    return sdata

data=fetchOHLC(ticker,'1',3)
print(data)


import mplfinance as mpf
brick_size=20
calculated_values = {}
mpf.plot(data, type='renko', renko_params=dict(brick_size=brick_size),return_calculated_values=calculated_values,returnfig=False,style='yahoo')
renko_df = pd.DataFrame(calculated_values)
renko_df=renko_df[["renko_dates",'renko_bricks']]



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
print(renko_df)
# renko_df.to_csv('renko.csv')





def candle_renko_refresh(ticker,brick_size=3):
    # global paper_option_data_info
    # brick_size=paper_option_data_info.get(ticker).get('brick_size')
    # brick_size=3
    data=fetchOHLC(ticker,'1',5)          
    calculated_values = {}

    mpf.plot(data, type='renko', renko_params=dict(brick_size=brick_size),return_calculated_values=calculated_values,returnfig=True,style='yahoo')

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

    print(renko_df[["renko_dates",'renko_bricks','pos_count','ema','trend']].tail(20))
    n_brick=renko_df['pos_count'].iloc[-1]
    print(n_brick,last)

    # paper_option_data_info.get(ticker).update({'brick_no':n_brick,'brick_last':last})


candle_renko_refresh('NSE:KOTAKBANK-EQ',brick_size=3)
