#iron condor with adjustment to butterfly
#credit https://www.youtube.com/watch?v=p8kNYf3qfbo
#get atm price from spot (18200)
#buy 400 points otm call and put for hedge (buy 18800 put and 18600 call)
#sell 200 point otm call and put (sell 18000 put and 18400 call)
#if spot moves by 100 point make adjustment (18100)
#book profit making leg (close 18400 call and 18600 call)
#sell 100 point otm call along with hedge (sell 18200 call and buy 18400 call )
#if spot moves by 100 point again  make adjustment (18000)
#close your profit making leg (close 18200 call and 18400 call)
#sell atm call and buy hedge(sell 18000 call and buy 18200 call)
#we have converted our iron condor to iron butterfly
#close everything at 15:15



from fyers_apiv3 import fyersModel
from fyers_apiv3.FyersWebsocket import data_ws
from fyers_apiv3.FyersWebsocket import order_ws
import pandas as pd
import datetime as dt
import asyncio
import pytz
import pickle
import time
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

import logging
logging.basicConfig(level=logging.INFO, filename=f'option_selling_{dt.date.today()}',filemode='a',format="%(asctime)s - %(message)s")

index_name='NIFTY'
ticker=f"NSE:{index_name}-INDEX"
# ticker='MCX:CRUDEOIL24DECFUT'
strike_count=10
strike_diff=50
account_type='PAPER'


start_hour,start_min=10,1
end_hour,end_min=15,10
quantity=25

buy_points=400
sell_points=200
spot_move=100


ct=dt.datetime.now()
start_time=dt.datetime(ct.year,ct.month,ct.day,start_hour,start_min)
end_time=dt.datetime(ct.year,ct.month,ct.day,end_hour,end_min)

fyers = fyersModel.FyersModel(client_id=client_id, is_async=False, token=access_token, log_path="")
fyers_asysc = fyersModel.FyersModel(client_id=client_id, is_async=True, token=access_token, log_path="")


data = {
    "symbol":ticker,
    "strikecount":strike_count,
    "timestamp": ""
}

#getting expiry
response = fyers.optionchain(data=data)['data']
print(response)
print(pd.DataFrame(response['expiryData']))
expiry=response['expiryData'][0]['date']
print(expiry)
expiry_e=response['expiryData'][0]['expiry']



#get open price

f = dt.date.today() - dt.timedelta(5)
p = dt.date.today()

data = {
    "symbol": ticker,
    "resolution": "D",
    "date_format": "1",
    "range_from": f.strftime('%Y-%m-%d'),
    "range_to": p.strftime('%Y-%m-%d'),
    "cont_flag": "1"
}


# Fetch historical data
response2 =fyers.history(data=data)
hist_data = pd.DataFrame(response2['candles'])
hist_data.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
ist = pytz.timezone('Asia/Kolkata')
hist_data['date'] = pd.to_datetime(hist_data['date'], unit='s').dt.tz_localize('UTC').dt.tz_convert(ist)
hist_data=hist_data[hist_data['date'].dt.date<ct.date()]
print(hist_data)

#calculate pivot



# option chain
data = {
    "symbol":ticker,
    "strikecount":strike_count,
    "timestamp":expiry_e
}

response = fyers.optionchain(data=data)['data']
option_chain=pd.DataFrame(response['optionsChain'])
symbols=option_chain['symbol'].to_list()

l1=['NSE:INDIAVIX-INDEX']
call_list=[]
put_list=[]
for s in symbols:
    if s.endswith('CE'):
        call_list.append(s)
    else:
        put_list.append(s)

symbols=put_list+call_list
symbols.append(l1[0])
print(symbols)


df=pd.DataFrame(columns=['name','ltp','ch','chp','avg_trade_price','open_price','high_price','low_price','prev_close_price','vol_traded_today','oi','pdoi','oipercent','bid_price','ask_price','last_traded_time','exch_feed_time','bid_size','ask_size','last_traded_qty','tot_buy_qty','tot_sell_qty','lower_ckt','upper_ckt','type','symbol','expiry' ])
df['name']=symbols
df.set_index('name',inplace=True)

print(df)

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

def get_otm_option(spot_price, side,points=100):   
    if side=='CE':
        otm_strike=(round(spot_price/strike_diff)*strike_diff)+points
    else:
        otm_strike=(round(spot_price/strike_diff)*strike_diff)-points
    # print(option_chain)
    # print(otm_strike)
    otm_option=option_chain[(option_chain['strike_price']==otm_strike) & (option_chain['option_type']==side) ]['symbol'].squeeze()
    return otm_option,otm_strike


position_df=get_position()
order_df=get_order()    

# print(position_df)
# print(order_df)

print(option_chain['ltp'].iloc[0])

sell_call_option,call_sell_strike=get_otm_option(option_chain['ltp'].iloc[0], 'CE',sell_points)
sell_put_option,put_sell_strike=get_otm_option(option_chain['ltp'].iloc[0], 'PE',sell_points)
print(sell_call_option,sell_put_option)

hedge_call_option,call_buy_strike=get_otm_option(option_chain['ltp'].iloc[0], 'CE',buy_points)
hedge_put_option,put_buy_strike=get_otm_option(option_chain['ltp'].iloc[0], 'PE',buy_points)
print(hedge_call_option,hedge_put_option)

def store(data,account_type):
    pickle.dump(data,open(f'data-{dt.date.today()}-{account_type}.pickle','wb'))

def load(account_type):
    return pickle.load(open(f'data-{dt.date.today()}-{account_type}.pickle', 'rb'))

if account_type=='PAPER':
    try:
        paper_option_data_info=load(account_type)

    except:
        column_names = ['time','ticker','price','action','stop_price','take_profit','spot_price','quantity']
        filled_df = pd.DataFrame(columns=column_names)
        filled_df.set_index('time',inplace=True)
        paper_option_data_info={'call_buy':{'name':hedge_call_option,'flag':0,'buy_price':0,'stop_price':0,'profit_price':0,'filled_df':filled_df.copy(),'spot':0,'quantity':0,'strike':0},
                                'put_buy':{'name':hedge_put_option,'flag':0,'buy_price':0,'stop_price':0,'profit_price':0,'filled_df':filled_df.copy(),'spot':0,'quantity':0,'strike':0},
                                
                                'call_sell':{'name':sell_call_option,'flag':0,'sell_price':0,'stop_price':0,'profit_price':0,'filled_df':filled_df.copy(),'spot':0,'quantity':0,'strike':0},
                                'put_sell':{'name':sell_put_option,'flag':0,'sell_price':0,'stop_price':0,'profit_price':0,'filled_df':filled_df.copy(),'spot':0,'quantity':0,'strike':0},

                                "main_flag":0,
                                'enter_spot_price':0,
                                'initial_spot_price':0,
                                'filled_df':filled_df
                                }

        
else:
    try:
        live_option_data_info=load(account_type)

    except:
        column_names = ['time','ticker','price','action','stop_price','take_profit','spot_price','quantity']
        filled_df = pd.DataFrame(columns=column_names)
        filled_df.set_index('time',inplace=True)
        live_option_data_info={'call_buy':{'name':hedge_call_option,'flag':0,'buy_price':0,'stop_price':0,'profit_price':0,'filled_df':filled_df.copy(),'spot':0,'quantity':0,'strike':0},
                                'put_buy':{'name':hedge_put_option,'flag':0,'buy_price':0,'stop_price':0,'profit_price':0,'filled_df':filled_df.copy(),'spot':0,'quantity':0,'strike':0},
                                
                                'call_sell':{'name':sell_call_option,'flag':0,'sell_price':0,'stop_price':0,'profit_price':0,'filled_df':filled_df.copy(),'spot':0,'quantity':0,'strike':0},
                                'put_sell':{'name':sell_put_option,'flag':0,'sell_price':0,'stop_price':0,'profit_price':0,'filled_df':filled_df.copy(),'spot':0,'quantity':0,'strike':0},

                                "main_flag":0,
                                'enter_spot_price':0,
                                'initial_spot_price':0,
                                'filled_df':filled_df
                                }

logging.info('started')



def paper_order():
    global quantity
    global paper_option_data_info
    global df
    global spot_price
    # spot_price=df[df['symbol']==ticker]['ltp'].iloc[0]
    spot_price=df.loc[ticker,'ltp']
    print(f"spot is {spot_price} ")
    print(f'initial spot price is {paper_option_data_info.get('initial_spot_price')}')
    ct=dt.datetime.now()
    # print(df)
    if ct>start_time:

        #name
        call_buy_name=paper_option_data_info.get('call_buy').get('name')
        put_buy_name=paper_option_data_info.get('put_buy').get('name')
        call_sell_name=paper_option_data_info.get('call_sell').get('name')
        put_sell_name=paper_option_data_info.get('put_sell').get('name')

        #flag
        call_buy_flag=paper_option_data_info.get('call_buy').get('flag')
        put_buy_flag=paper_option_data_info.get('put_buy').get('flag')
        call_sell_flag=paper_option_data_info.get('call_sell').get('flag')
        put_sell_flag=paper_option_data_info.get('put_sell').get('flag')

        #buy_price
        call_buy_price=paper_option_data_info.get('call_buy').get('buy_price')
        put_buy_price=paper_option_data_info.get('put_buy').get('buy_price')
        call_sell_price=paper_option_data_info.get('call_sell').get('sell_price')
        put_sell_price=paper_option_data_info.get('put_sell').get('sell_price')

        # print(call_buy_name,put_buy_name,call_sell_name,put_sell_name)
        #current price
        call_buy_current_price=df.loc[call_buy_name,'ltp']
        put_buy_current_price=df.loc[put_buy_name,'ltp']
        call_sell_current_price=df.loc[call_sell_name,'ltp']
        put_sell_current_price=df.loc[put_sell_name,'ltp']


        main_flag=paper_option_data_info['main_flag']
        enter_spot_price=paper_option_data_info['enter_spot_price']
        print("main flag",main_flag,enter_spot_price)

        #we have reached end time
        if ct>end_time:
            print('closing everything')
            #close call buy
            if call_buy_flag==1:
                a=[call_buy_name,call_buy_current_price,'SELL',0,0,spot_price,0] 
                paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                paper_option_data_info['call_buy']['flag']=5
                paper_option_data_info['call_buy']['quantity']=0
                time.sleep(1)

            #close put buy
            if put_buy_flag==1:
                a=[put_buy_name,put_buy_current_price,'SELL',0,0,spot_price,0]
                paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                paper_option_data_info['put_buy']['flag']=5
                paper_option_data_info['put_buy']['quantity']=0
                time.sleep(1)
            
            #close call sell
            if call_sell_flag==1:
                a=[call_sell_name,call_sell_current_price,'BUY',0,0,spot_price,0]
                paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                paper_option_data_info['call_sell']['flag']=5
                paper_option_data_info['call_sell']['quantity']=0
                time.sleep(1)
            
            #close put sell
            if put_sell_flag==1:
                a=[put_sell_name,put_sell_current_price,'BUY',0,0,spot_price,0]
                paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                paper_option_data_info['put_sell']['flag']=5
                paper_option_data_info['put_sell']['quantity']=0
                time.sleep(1)
    


        #condition satisfied
        if main_flag==0:
            logging.info('placing iron condor ')  
            
            #buying hedges first
            call_buy_name,strike=get_otm_option(spot_price, 'CE',buy_points)
            paper_option_data_info['call_buy']['name']=call_buy_name
            paper_option_data_info['call_buy']['quantity']=quantity
            paper_option_data_info['call_buy']['strike']=strike

            put_buy_name,strike=get_otm_option(spot_price, 'PE', buy_points)
            paper_option_data_info['put_buy']['name']=put_buy_name
            paper_option_data_info['put_buy']['quantity']=quantity
            paper_option_data_info['put_buy']['strike']=strike

            call_buy_current_price=df.loc[call_buy_name,'ltp']
            put_buy_current_price=df.loc[put_buy_name,'ltp']


            paper_option_data_info['call_buy']['buy_price']=call_buy_current_price
            paper_option_data_info['put_buy']['buy_price']=put_buy_current_price

            a=[call_buy_name,call_buy_current_price,'BUY',0,0,spot_price,quantity] 
            paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a
            paper_option_data_info['call_buy']['flag']=1

            b=[put_buy_name,put_buy_current_price,'BUY',0,0,spot_price,quantity] 
            paper_option_data_info['filled_df'].loc[dt.datetime.now()] = b
            paper_option_data_info['put_buy']['flag']=1

            time.sleep(1)

            #selling legs
            call_sell_name,strike=get_otm_option(spot_price, 'CE', sell_points)
            paper_option_data_info['call_sell']['name']=call_sell_name
            paper_option_data_info['call_sell']['quantity']=quantity
            paper_option_data_info['call_sell']['strike']=strike

            put_sell_name,strike=get_otm_option(spot_price, 'PE', sell_points)
            paper_option_data_info['put_sell']['name']=put_sell_name
            paper_option_data_info['put_sell']['quantity']=quantity
            paper_option_data_info['put_sell']['strike']=strike

            call_sell_current_price=df.loc[call_sell_name,'ltp']
            put_sell_current_price=df.loc[put_sell_name,'ltp']

   
            paper_option_data_info['call_sell']['sell_price']=call_sell_current_price
            paper_option_data_info['put_sell']['sell_price']=put_sell_current_price

            a=[call_sell_name,call_sell_current_price,'SELL',0,0,spot_price,quantity]
            paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a
            paper_option_data_info['call_sell']['flag']=1

            b=[put_sell_name,put_sell_current_price,'SELL',0,0,spot_price,quantity]
            paper_option_data_info['filled_df'].loc[dt.datetime.now()] = b
            paper_option_data_info['put_sell']['flag']=1

            paper_option_data_info['enter_spot_price']=spot_price
            paper_option_data_info['initial_spot_price']=spot_price
            paper_option_data_info['main_flag']=1
            print('done placing condor')

   
        elif (main_flag==1)  :

            if spot_price<enter_spot_price-spot_move:
                #close call buy leg
                a=[call_buy_name,call_buy_current_price,'SELL',0,0,spot_price,quantity] 
                paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                time.sleep(1)
    

                #close call sell leg
                a=[call_sell_name,call_sell_current_price,'BUY',0,0,spot_price,quantity]
                paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a

                time.sleep(1)


                #open call buy leg
                s=(paper_option_data_info['call_buy']['strike']-spot_move*2)
                call_buy_name=option_chain[(option_chain['strike_price']==s) & (option_chain['option_type']=='CE') ]['symbol'].squeeze()
                paper_option_data_info['call_buy']['name']=call_buy_name
                paper_option_data_info['call_buy']['quantity']=quantity
                paper_option_data_info['call_buy']['strike']=s
                call_buy_current_price=df.loc[call_buy_name,'ltp']
                paper_option_data_info['call_buy']['buy_price']=call_buy_current_price
                a=[call_buy_name,call_buy_current_price,'BUY',0,0,spot_price,quantity] 
                paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                paper_option_data_info['call_buy']['flag']=1
                time.sleep(1)

                #open call sell leg
                s=(paper_option_data_info['call_sell']['strike']-spot_move*2)
                call_sell_name=option_chain[(option_chain['strike_price']==s) & (option_chain['option_type']=='CE') ]['symbol'].squeeze()
                paper_option_data_info['call_sell']['name']=call_sell_name
                paper_option_data_info['call_sell']['quantity']=quantity
                paper_option_data_info['call_sell']['strike']=s
                call_sell_current_price=df.loc[call_sell_name,'ltp']
                paper_option_data_info['call_sell']['sell_price']=call_sell_current_price
                a=[call_sell_name,call_sell_current_price,'SELL',0,0,spot_price,quantity]
                paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                paper_option_data_info['call_sell']['flag']=1
                
                paper_option_data_info['enter_spot_price']=spot_price
                paper_option_data_info['main_flag']=2
                print('done doing adjustment')
        
            elif spot_price>enter_spot_price+spot_move:
                    #close put buy leg
                    a=[put_buy_name,put_buy_current_price,'SELL',0,0,spot_price,quantity]
                    paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a

                    #close put sell leg
                    a=[put_sell_name,put_sell_current_price,'BUY',0,0,spot_price,quantity]
                    paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a

                    #open put buy leg
                    s=(paper_option_data_info['put_buy']['strike']+spot_move*2)
                    put_buy_name=option_chain[(option_chain['strike_price']==s) & (option_chain['option_type']=='PE') ]['symbol'].squeeze()
                    paper_option_data_info['put_buy']['name']=put_buy_name
                    paper_option_data_info['put_buy']['quantity']=quantity
                    paper_option_data_info['put_buy']['strike']=s
                    put_buy_current_price=df.loc[put_buy_name,'ltp']
                    paper_option_data_info['put_buy']['buy_price']=put_buy_current_price
                    a=[put_buy_name,put_buy_current_price,'BUY',0,0,spot_price,quantity]
                    paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                    paper_option_data_info['put_buy']['flag']=1

                    #open put sell leg
                    s=(paper_option_data_info['put_sell']['strike']+spot_move*2)
                    put_sell_name=option_chain[(option_chain['strike_price']==s) & (option_chain['option_type']=='PE') ]['symbol'].squeeze()
                    paper_option_data_info['put_sell']['name']=put_sell_name
                    paper_option_data_info['put_sell']['quantity']=quantity
                    paper_option_data_info['put_sell']['strike']=(s)
                    put_sell_current_price=df.loc[put_sell_name,'ltp']
                    paper_option_data_info['put_sell']['sell_price']=put_sell_current_price
                    a=[put_sell_name,put_sell_current_price,'SELL',0,0,spot_price,quantity]
                    paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                    paper_option_data_info['put_sell']['flag']=1

                    paper_option_data_info['enter_spot_price']=spot_price
                    paper_option_data_info['main_flag']=2
                    print('done doing adjustment')    


        elif (main_flag==2):

            if spot_price<enter_spot_price-spot_move:
                #close call buy leg
                a=[call_buy_name,call_buy_current_price,'SELL',0,0,spot_price,quantity] 
                paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                time.sleep(1)
    

                #close call sell leg
                a=[call_sell_name,call_sell_current_price,'BUY',0,0,spot_price,quantity]
                paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a

                time.sleep(1)


                #open call buy leg
                s=(paper_option_data_info['call_buy']['strike']-spot_move*2)
                call_buy_name=option_chain[(option_chain['strike_price']==s) & (option_chain['option_type']=='CE') ]['symbol'].squeeze()
                paper_option_data_info['call_buy']['name']=call_buy_name
                paper_option_data_info['call_buy']['quantity']=quantity
                paper_option_data_info['call_buy']['strike']=s
                call_buy_current_price=df.loc[call_buy_name,'ltp']
                paper_option_data_info['call_buy']['buy_price']=call_buy_current_price
                a=[call_buy_name,call_buy_current_price,'BUY',0,0,spot_price,quantity] 
                paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                paper_option_data_info['call_buy']['flag']=1
                time.sleep(1)
                #open call sell leg
                s=(paper_option_data_info['call_sell']['strike']-spot_move*2)
                call_sell_name=option_chain[(option_chain['strike_price']==s) & (option_chain['option_type']=='CE') ]['symbol'].squeeze()
                paper_option_data_info['call_sell']['name']=call_sell_name
                paper_option_data_info['call_sell']['quantity']=quantity
                paper_option_data_info['call_sell']['strike']=s
                call_sell_current_price=df.loc[call_sell_name,'ltp']
                paper_option_data_info['call_sell']['sell_price']=call_sell_current_price
                a=[call_sell_name,call_sell_current_price,'SELL',0,0,spot_price,quantity]
                paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                paper_option_data_info['call_sell']['flag']=1
                
                paper_option_data_info['enter_spot_price']=spot_price
                paper_option_data_info['main_flag']=3
                print('done doing adjustment')
        
            elif spot_price>enter_spot_price+spot_move:
                    #close put buy leg
                    a=[put_buy_name,put_buy_current_price,'SELL',0,0,spot_price,quantity]
                    paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a

                    #close put sell leg
                    a=[put_sell_name,put_sell_current_price,'BUY',0,0,spot_price,quantity]
                    paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a

                    #open put buy leg
                    s=(paper_option_data_info['put_buy']['strike']+spot_move*2)
                    put_buy_name=option_chain[(option_chain['strike_price']==s) & (option_chain['option_type']=='PE') ]['symbol'].squeeze()
                    paper_option_data_info['put_buy']['name']=put_buy_name
                    paper_option_data_info['put_buy']['quantity']=quantity
                    paper_option_data_info['put_buy']['strike']=s
                    put_buy_current_price=df.loc[put_buy_name,'ltp']
                    paper_option_data_info['put_buy']['buy_price']=put_buy_current_price
                    a=[put_buy_name,put_buy_current_price,'BUY',0,0,spot_price,quantity]
                    paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                    paper_option_data_info['put_buy']['flag']=1

                    #open put sell leg
                    s=(paper_option_data_info['put_sell']['strike']+spot_move*2)
                    put_sell_name=option_chain[(option_chain['strike_price']==s) & (option_chain['option_type']=='PE') ]['symbol'].squeeze()
                    paper_option_data_info['put_sell']['name']=put_sell_name
                    paper_option_data_info['put_sell']['quantity']=quantity
                    paper_option_data_info['put_sell']['strike']=(s)
                    put_sell_current_price=df.loc[put_sell_name,'ltp']
                    paper_option_data_info['put_sell']['sell_price']=put_sell_current_price
                    a=[put_sell_name,put_sell_current_price,'SELL',0,0,spot_price,quantity]
                    paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                    paper_option_data_info['put_sell']['flag']=1

                    paper_option_data_info['enter_spot_price']=spot_price
                    paper_option_data_info['main_flag']=3
                    print('done doing adjustment')    


        elif (main_flag==3):

            if (spot_price<(paper_option_data_info['initial_spot_price']-(3*spot_move))) or (spot_price>(paper_option_data_info['initial_spot_price']+(3*spot_move))):

                print('closing everything')
                #close call buy
                if call_buy_flag==1:
                    a=[call_buy_name,call_buy_current_price,'SELL',0,0,spot_price,0] 
                    paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                    paper_option_data_info['call_buy']['flag']=5
                    paper_option_data_info['call_buy']['quantity']=0
                    time.sleep(1)

                #close put buy
                if put_buy_flag==1:
                    a=[put_buy_name,put_buy_current_price,'SELL',0,0,spot_price,0]
                    paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                    paper_option_data_info['put_buy']['flag']=5
                    paper_option_data_info['put_buy']['quantity']=0
                    time.sleep(1)
                
                #close call sell
                if call_sell_flag==1:
                    a=[call_sell_name,call_sell_current_price,'BUY',0,0,spot_price,0]
                    paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                    paper_option_data_info['call_sell']['flag']=5
                    paper_option_data_info['call_sell']['quantity']=0
                    time.sleep(1)
                
                #close put sell
                if put_sell_flag==1:
                    a=[put_sell_name,put_sell_current_price,'BUY',0,0,spot_price,0]
                    paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                    paper_option_data_info['put_sell']['flag']=5
                    paper_option_data_info['put_sell']['quantity']=0
                    time.sleep(1)
      


        #update dataframe
        if not paper_option_data_info['filled_df'].empty:
            paper_option_data_info['filled_df'].to_csv(f'trades_{dt.date.today()}.csv')    
        


        store(paper_option_data_info,account_type)


def real_order():
    global quantity
    global live_option_data_info
    global df
    global spot_price
    # spot_price=df[df['symbol']==ticker]['ltp'].iloc[0]
    spot_price=df.loc[ticker,'ltp']
    print(f"spot is {spot_price} ")
    print(f'initial spot price is {live_option_data_info.get('initial_spot_price')}')
    ct=dt.datetime.now()
    # print(df)
    if ct>start_time:

        #name
        call_buy_name=live_option_data_info.get('call_buy').get('name')
        put_buy_name=live_option_data_info.get('put_buy').get('name')
        call_sell_name=live_option_data_info.get('call_sell').get('name')
        put_sell_name=live_option_data_info.get('put_sell').get('name')

        #flag
        call_buy_flag=live_option_data_info.get('call_buy').get('flag')
        put_buy_flag=live_option_data_info.get('put_buy').get('flag')
        call_sell_flag=live_option_data_info.get('call_sell').get('flag')
        put_sell_flag=live_option_data_info.get('put_sell').get('flag')

        #buy_price
        call_buy_price=live_option_data_info.get('call_buy').get('buy_price')
        put_buy_price=live_option_data_info.get('put_buy').get('buy_price')
        call_sell_price=live_option_data_info.get('call_sell').get('sell_price')
        put_sell_price=live_option_data_info.get('put_sell').get('sell_price')

        # print(call_buy_name,put_buy_name,call_sell_name,put_sell_name)
        #current price
        call_buy_current_price=df.loc[call_buy_name,'ltp']
        put_buy_current_price=df.loc[put_buy_name,'ltp']
        call_sell_current_price=df.loc[call_sell_name,'ltp']
        put_sell_current_price=df.loc[put_sell_name,'ltp']


        main_flag=live_option_data_info['main_flag']
        enter_spot_price=live_option_data_info['enter_spot_price']
        print("main flag",main_flag,enter_spot_price)

        #we have reached end time
        if ct>end_time:
            print('closing everything')
            #close call buy
            if call_buy_flag==1:
                    a=[call_buy_name,call_buy_current_price,'SELL',0,0,spot_price,0] 
                    live_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                    live_option_data_info['call_buy']['flag']=5
                    live_option_data_info['call_buy']['quantity']=0
                    time.sleep(1)

            #close put buy
            if put_buy_flag==1:
                a=[put_buy_name,put_buy_current_price,'SELL',0,0,spot_price,0]
                live_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                live_option_data_info['put_buy']['flag']=5
                live_option_data_info['put_buy']['quantity']=0
                time.sleep(1)
            
            #close call sell
            if call_sell_flag==1:
                a=[call_sell_name,call_sell_current_price,'BUY',0,0,spot_price,0]
                live_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                live_option_data_info['call_sell']['flag']=5
                live_option_data_info['call_sell']['quantity']=0
                time.sleep(1)
            
            #close put sell
            if put_sell_flag==1:
                a=[put_sell_name,put_sell_current_price,'BUY',0,0,spot_price,0]
                live_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                live_option_data_info['put_sell']['flag']=5
                live_option_data_info['put_sell']['quantity']=0
                time.sleep(1)
    


        #condition satisfied
        if main_flag==0:
            logging.info('placing iron condor ')  
            
            #buying hedges first
            call_buy_name,strike=get_otm_option(spot_price, 'CE',buy_points)
            live_option_data_info['call_buy']['name']=call_buy_name
            live_option_data_info['call_buy']['quantity']=quantity
            live_option_data_info['call_buy']['strike']=strike

            put_buy_name,strike=get_otm_option(spot_price, 'PE', buy_points)
            live_option_data_info['put_buy']['name']=put_buy_name
            live_option_data_info['put_buy']['quantity']=quantity
            live_option_data_info['put_buy']['strike']=strike

            call_buy_current_price=df.loc[call_buy_name,'ltp']
            put_buy_current_price=df.loc[put_buy_name,'ltp']


            live_option_data_info['call_buy']['buy_price']=call_buy_current_price
            live_option_data_info['put_buy']['buy_price']=put_buy_current_price

            a=[call_buy_name,call_buy_current_price,'BUY',0,0,spot_price,quantity] 
            live_option_data_info['filled_df'].loc[dt.datetime.now()] = a
            live_option_data_info['call_buy']['flag']=1

            b=[put_buy_name,put_buy_current_price,'BUY',0,0,spot_price,quantity] 
            live_option_data_info['filled_df'].loc[dt.datetime.now()] = b
            live_option_data_info['put_buy']['flag']=1

            time.sleep(1)

            #selling legs
            call_sell_name,strike=get_otm_option(spot_price, 'CE', sell_points)
            live_option_data_info['call_sell']['name']=call_sell_name
            live_option_data_info['call_sell']['quantity']=quantity
            live_option_data_info['call_sell']['strike']=strike

            put_sell_name,strike=get_otm_option(spot_price, 'PE', sell_points)
            live_option_data_info['put_sell']['name']=put_sell_name
            live_option_data_info['put_sell']['quantity']=quantity
            live_option_data_info['put_sell']['strike']=strike

            call_sell_current_price=df.loc[call_sell_name,'ltp']
            put_sell_current_price=df.loc[put_sell_name,'ltp']

   
            live_option_data_info['call_sell']['sell_price']=call_sell_current_price
            live_option_data_info['put_sell']['sell_price']=put_sell_current_price

            a=[call_sell_name,call_sell_current_price,'SELL',0,0,spot_price,quantity]
            live_option_data_info['filled_df'].loc[dt.datetime.now()] = a
            live_option_data_info['call_sell']['flag']=1

            b=[put_sell_name,put_sell_current_price,'SELL',0,0,spot_price,quantity]
            live_option_data_info['filled_df'].loc[dt.datetime.now()] = b
            live_option_data_info['put_sell']['flag']=1

            live_option_data_info['enter_spot_price']=spot_price
            live_option_data_info['initial_spot_price']=spot_price
            live_option_data_info['main_flag']=1
            print('done placing condor')

   
        elif (main_flag==1)  :

            if spot_price<enter_spot_price-spot_move:
                #close call buy leg
                a=[call_buy_name,call_buy_current_price,'SELL',0,0,spot_price,quantity] 
                live_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                time.sleep(1)
    

                #close call sell leg
                a=[call_sell_name,call_sell_current_price,'BUY',0,0,spot_price,quantity]
                live_option_data_info['filled_df'].loc[dt.datetime.now()] = a

                time.sleep(1)


                #open call buy leg
                s=(live_option_data_info['call_buy']['strike']-spot_move*2)
                call_buy_name=option_chain[(option_chain['strike_price']==s) & (option_chain['option_type']=='CE') ]['symbol'].squeeze()
                live_option_data_info['call_buy']['name']=call_buy_name
                live_option_data_info['call_buy']['quantity']=quantity
                live_option_data_info['call_buy']['strike']=s
                call_buy_current_price=df.loc[call_buy_name,'ltp']
                live_option_data_info['call_buy']['buy_price']=call_buy_current_price
                a=[call_buy_name,call_buy_current_price,'BUY',0,0,spot_price,quantity] 
                live_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                live_option_data_info['call_buy']['flag']=1
                time.sleep(1)

                #open call sell leg
                s=(live_option_data_info['call_sell']['strike']-spot_move*2)
                call_sell_name=option_chain[(option_chain['strike_price']==s) & (option_chain['option_type']=='CE') ]['symbol'].squeeze()
                live_option_data_info['call_sell']['name']=call_sell_name
                live_option_data_info['call_sell']['quantity']=quantity
                live_option_data_info['call_sell']['strike']=s
                call_sell_current_price=df.loc[call_sell_name,'ltp']
                live_option_data_info['call_sell']['sell_price']=call_sell_current_price
                a=[call_sell_name,call_sell_current_price,'SELL',0,0,spot_price,quantity]
                live_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                live_option_data_info['call_sell']['flag']=1
                
                live_option_data_info['enter_spot_price']=spot_price
                live_option_data_info['main_flag']=2
                print('done doing adjustment')
        
            elif spot_price>enter_spot_price+spot_move:
                    #close put buy leg
                    a=[put_buy_name,put_buy_current_price,'SELL',0,0,spot_price,quantity]
                    live_option_data_info['filled_df'].loc[dt.datetime.now()] = a

                    #close put sell leg
                    a=[put_sell_name,put_sell_current_price,'BUY',0,0,spot_price,quantity]
                    live_option_data_info['filled_df'].loc[dt.datetime.now()] = a

                    #open put buy leg
                    s=(live_option_data_info['put_buy']['strike']+spot_move*2)
                    put_buy_name=option_chain[(option_chain['strike_price']==s) & (option_chain['option_type']=='PE') ]['symbol'].squeeze()
                    live_option_data_info['put_buy']['name']=put_buy_name
                    live_option_data_info['put_buy']['quantity']=quantity
                    live_option_data_info['put_buy']['strike']=s
                    put_buy_current_price=df.loc[put_buy_name,'ltp']
                    live_option_data_info['put_buy']['buy_price']=put_buy_current_price
                    a=[put_buy_name,put_buy_current_price,'BUY',0,0,spot_price,quantity]
                    live_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                    live_option_data_info['put_buy']['flag']=1

                    #open put sell leg
                    s=(live_option_data_info['put_sell']['strike']+spot_move*2)
                    put_sell_name=option_chain[(option_chain['strike_price']==s) & (option_chain['option_type']=='PE') ]['symbol'].squeeze()
                    live_option_data_info['put_sell']['name']=put_sell_name
                    live_option_data_info['put_sell']['quantity']=quantity
                    live_option_data_info['put_sell']['strike']=(s)
                    put_sell_current_price=df.loc[put_sell_name,'ltp']
                    live_option_data_info['put_sell']['sell_price']=put_sell_current_price
                    a=[put_sell_name,put_sell_current_price,'SELL',0,0,spot_price,quantity]
                    live_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                    live_option_data_info['put_sell']['flag']=1

                    live_option_data_info['enter_spot_price']=spot_price
                    live_option_data_info['main_flag']=2
                    print('done doing adjustment')    


        elif (main_flag==2):

            if spot_price<enter_spot_price-spot_move:
                #close call buy leg
                a=[call_buy_name,call_buy_current_price,'SELL',0,0,spot_price,quantity] 
                live_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                time.sleep(1)
    

                #close call sell leg
                a=[call_sell_name,call_sell_current_price,'BUY',0,0,spot_price,quantity]
                live_option_data_info['filled_df'].loc[dt.datetime.now()] = a

                time.sleep(1)


                #open call buy leg
                s=(live_option_data_info['call_buy']['strike']-spot_move*2)
                call_buy_name=option_chain[(option_chain['strike_price']==s) & (option_chain['option_type']=='CE') ]['symbol'].squeeze()
                live_option_data_info['call_buy']['name']=call_buy_name
                live_option_data_info['call_buy']['quantity']=quantity
                live_option_data_info['call_buy']['strike']=s
                call_buy_current_price=df.loc[call_buy_name,'ltp']
                live_option_data_info['call_buy']['buy_price']=call_buy_current_price
                a=[call_buy_name,call_buy_current_price,'BUY',0,0,spot_price,quantity] 
                live_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                live_option_data_info['call_buy']['flag']=1
                time.sleep(1)
                #open call sell leg
                s=(live_option_data_info['call_sell']['strike']-spot_move*2)
                call_sell_name=option_chain[(option_chain['strike_price']==s) & (option_chain['option_type']=='CE') ]['symbol'].squeeze()
                live_option_data_info['call_sell']['name']=call_sell_name
                live_option_data_info['call_sell']['quantity']=quantity
                live_option_data_info['call_sell']['strike']=s
                call_sell_current_price=df.loc[call_sell_name,'ltp']
                live_option_data_info['call_sell']['sell_price']=call_sell_current_price
                a=[call_sell_name,call_sell_current_price,'SELL',0,0,spot_price,quantity]
                live_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                live_option_data_info['call_sell']['flag']=1
                
                live_option_data_info['enter_spot_price']=spot_price
                live_option_data_info['main_flag']=3
                print('done doing adjustment')
        
            elif spot_price>enter_spot_price+spot_move:
                    #close put buy leg
                    a=[put_buy_name,put_buy_current_price,'SELL',0,0,spot_price,quantity]
                    live_option_data_info['filled_df'].loc[dt.datetime.now()] = a

                    #close put sell leg
                    a=[put_sell_name,put_sell_current_price,'BUY',0,0,spot_price,quantity]
                    live_option_data_info['filled_df'].loc[dt.datetime.now()] = a

                    #open put buy leg
                    s=(live_option_data_info['put_buy']['strike']+spot_move*2)
                    put_buy_name=option_chain[(option_chain['strike_price']==s) & (option_chain['option_type']=='PE') ]['symbol'].squeeze()
                    live_option_data_info['put_buy']['name']=put_buy_name
                    live_option_data_info['put_buy']['quantity']=quantity
                    live_option_data_info['put_buy']['strike']=s
                    put_buy_current_price=df.loc[put_buy_name,'ltp']
                    live_option_data_info['put_buy']['buy_price']=put_buy_current_price
                    a=[put_buy_name,put_buy_current_price,'BUY',0,0,spot_price,quantity]
                    live_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                    live_option_data_info['put_buy']['flag']=1

                    #open put sell leg
                    s=(live_option_data_info['put_sell']['strike']+spot_move*2)
                    put_sell_name=option_chain[(option_chain['strike_price']==s) & (option_chain['option_type']=='PE') ]['symbol'].squeeze()
                    live_option_data_info['put_sell']['name']=put_sell_name
                    live_option_data_info['put_sell']['quantity']=quantity
                    live_option_data_info['put_sell']['strike']=(s)
                    put_sell_current_price=df.loc[put_sell_name,'ltp']
                    live_option_data_info['put_sell']['sell_price']=put_sell_current_price
                    a=[put_sell_name,put_sell_current_price,'SELL',0,0,spot_price,quantity]
                    live_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                    live_option_data_info['put_sell']['flag']=1

                    live_option_data_info['enter_spot_price']=spot_price
                    live_option_data_info['main_flag']=3
                    print('done doing adjustment')    


        elif (main_flag==3):

            if (spot_price<(live_option_data_info['initial_spot_price']-(3*spot_move))) or (spot_price>(live_option_data_info['initial_spot_price']+(3*spot_move))):

                print('closing everything')
                #close call buy
                if call_buy_flag==1:
                    a=[call_buy_name,call_buy_current_price,'SELL',0,0,spot_price,0] 
                    live_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                    live_option_data_info['call_buy']['flag']=5
                    live_option_data_info['call_buy']['quantity']=0
                    time.sleep(1)

                #close put buy
                if put_buy_flag==1:
                    a=[put_buy_name,put_buy_current_price,'SELL',0,0,spot_price,0]
                    live_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                    live_option_data_info['put_buy']['flag']=5
                    live_option_data_info['put_buy']['quantity']=0
                    time.sleep(1)
                
                #close call sell
                if call_sell_flag==1:
                    a=[call_sell_name,call_sell_current_price,'BUY',0,0,spot_price,0]
                    live_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                    live_option_data_info['call_sell']['flag']=5
                    live_option_data_info['call_sell']['quantity']=0
                    time.sleep(1)
                
                #close put sell
                if put_sell_flag==1:
                    a=[put_sell_name,put_sell_current_price,'BUY',0,0,spot_price,0]
                    live_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                    live_option_data_info['put_sell']['flag']=5
                    live_option_data_info['put_sell']['quantity']=0
                    time.sleep(1)
      


        #update dataframe
        if not live_option_data_info['filled_df'].empty:
            live_option_data_info['filled_df'].to_csv(f'trades_{dt.date.today()}.csv')    
        


        store(live_option_data_info,account_type)


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

        #getting oi data every minute
        ct=dt.datetime.now()
        # if ct>end_time:
        #     print('close everything')
        #     data = {
        #         "segment":[11],
        #         "side":[1,-1],
        #         "productType":["INTRADAY","CNC"]
        #     }

        #     response = fyers.exit_positions(data=data)
        #     print(response)


        if ct.second in range(1,60,3):
            try:
                pos1=fyers.positions()
                pnl=int(pos1.get('overall').get('pl_total'))
            except:
                print('unable to fetch pnl')
            print(pnl)

        if ct.second == 1:
            #print('calling oi function')
            await get_quotes() 

        if df.shape[0]!=0:
            print(ct)
            
            # df.to_csv('real_time_data.csv')
            if account_type=='PAPER':
                paper_order()
            # else:
            #     real_order()

        await asyncio.sleep(1)


async def get_quotes():
        print('getting quotes')
        global symbols,df
        st=''
        for i in symbols:
            st+=i+','
        st=st[:-1]
        data = {
            "symbol":st,
            "ohlcv_flag":"1"
        }
        response = fyers.depth(data=data)
        # print(response)
        for i in symbols:
            oi=response['d'][i]["oi"]
            pdoi=response['d'][i]["pdoi"]
            oipercent=response['d'][i]["oipercent"]
            expiry=response['d'][i]["expiry"]
            df.at[i, 'oi'] = oi
            df.at[i, 'pdoi'] = pdoi
            df.at[i, 'oipercent'] = oipercent
            df.at[i, 'expiry'] = expiry
        #print(df)

time.sleep(5)

async def main():
    while True:
        await main_strategy_code()

asyncio.run(main())
