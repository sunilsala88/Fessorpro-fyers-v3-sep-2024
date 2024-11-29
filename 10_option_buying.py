


from fyers_apiv3 import fyersModel
from fyers_apiv3.FyersWebsocket import data_ws
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
logging.basicConfig(level=logging.INFO, filename=f'option_strategy_{dt.date.today()}',filemode='a',format="%(asctime)s - %(message)s")



index_name='NIFTYBANK'
ticker=f"NSE:{index_name}-INDEX"
# ticker='MCX:CRUDEOIL24DECFUT'
strike_count=10
strike_diff=100
account_type='PAPER'
buffer=5
profit_loss_point=30
start_hour,start_min=9,35
end_hour,end_min=22,15
quantity=15

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
# print(response)
# print(pd.DataFrame(response['expiryData']))
expiry=response['expiryData'][0]['date']
print(expiry)
expiry_e=response['expiryData'][0]['expiry']
print(expiry_e)



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

def calculate_cpr(high, low, close):
    """
    Calculate CPR levels.
    
    Parameters:
    high (float): The high price.
    low (float): The low price.
    close (float): The close price.
    
    Returns:
    dict: A dictionary containing Pivot, TC, and BC levels.
    """
    pivot = (high + low + close) / 3

    # Resistance Levels
    r1 = (2 * pivot) - low

    # Support Levels
    s1 = (2 * pivot) - high

    return int(pivot),int(r1),int(s1)

pivot,resistance,support = calculate_cpr(hist_data['high'].iloc[-1], hist_data['low'].iloc[-1], hist_data['close'].iloc[-1])
print(pivot,resistance,support)

pivot=51865

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
print(len(symbols))


df=pd.DataFrame(columns=['name','ltp','ch','chp','avg_trade_price','open_price','high_price','low_price','prev_close_price','vol_traded_today','oi','pdoi','oipercent','bid_price','ask_price','last_traded_time','exch_feed_time','bid_size','ask_size','last_traded_qty','tot_buy_qty','tot_sell_qty','lower_ckt','upper_ckt','type','symbol','expiry' ])
df['name']=symbols
df.set_index('name',inplace=True)

print(df)

def get_otm_option(spot_price, side,points=100):   
    if side=='CE':
        otm_strike=(round(spot_price/strike_diff)*strike_diff)+points
    else:
        otm_strike=(round(spot_price/strike_diff)*strike_diff)-points

    otm_option=option_chain[(option_chain['strike_price']==otm_strike) & (option_chain['option_type']==side) ]['symbol'].squeeze()
    return otm_option

n=get_otm_option(5848,'CE',100)
print(n)

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

call_option=get_otm_option(option_chain['ltp'].iloc[0], 'CE',100)
put_option=get_otm_option(option_chain['ltp'].iloc[0], 'PE',100)
print(call_option,put_option)


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
        paper_option_data_info={'call_buy':{'option_name':call_option,'trade_flag':0,'buy_price':0,'current_stop_price':0,'current_profit_price':0,'filled_df':filled_df.copy(),'underlying_price_level':0,'quantity':0,'pnl':0},
                                'put_buy':{'option_name':put_option,'trade_flag':0,'buy_price':0,'current_stop_price':0,'current_profit_price':0,'filled_df':filled_df.copy(),'underlying_price_level':0,'quantity':0,'pnl':0},
                                'condition':False
                                }

        
else:
    try:
        live_option_data_info=load(account_type)

    except:
        column_names = ['time','ticker','price','action','stop_price','take_profit','spot_price','quantity']
        filled_df = pd.DataFrame(columns=column_names)
        filled_df.set_index('time',inplace=True)
        live_option_data_info={'call_buy':{'option_name':call_option,'trade_flag':0,'buy_price':0,'current_stop_price':0,'current_profit_price':0,'filled_df':filled_df.copy(),'underlying_price_level':0,'quantity':0,'pnl':0},
                                'put_buy':{'option_name':put_option,'trade_flag':0,'buy_price':0,'current_stop_price':0,'current_profit_price':0,'filled_df':filled_df.copy(),'underlying_price_level':0,'quantity':0,'pnl':0},
                                'condition':False
                                }




def onmessage(ticks):
    global df
    # print(ticks)
    if ticks.get('symbol'):
        for key,value in ticks.items():
            #updating dataframe
            df.loc[ticks.get('symbol'), key] = value
            df.drop_duplicates(inplace=True)
            # print(df)

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

def paper_order():
    global quantity
    global paper_option_data_info
    global df
    global spot_price
    spot_price=df[df['symbol']==ticker]['ltp'].iloc[0]

    spot_price=df.loc[ticker,'ltp']
    print(f"spot is {spot_price} pivot is {pivot} support is {support} resistance is {resistance}")
    print(spot_price)
    ct=dt.datetime.now()
    if ct>start_time:

        # print(df)
        call_buy_trade_flag=paper_option_data_info['call_buy']['trade_flag']
        put_buy_trade_flag=paper_option_data_info['put_buy']['trade_flag']

        call_buy_stop_price=paper_option_data_info['call_buy']['current_stop_price']
        put_buy_stop_price=paper_option_data_info['put_buy']['current_stop_price']

        call_buy_profit_price=paper_option_data_info['call_buy']['current_profit_price']
        put_buy_profit_price=paper_option_data_info['put_buy']['current_profit_price']
        
        call_name=paper_option_data_info['call_buy']['option_name']
        put_name=paper_option_data_info['put_buy']['option_name']

        call_buy_price=paper_option_data_info['call_buy']['buy_price']
        put_buy_price=paper_option_data_info['put_buy']['buy_price']
        # print(call_name, put_name)
        # call_price=df[df['symbol']==call_name]['ltp'].iloc[0]
        call_price=df.loc[call_name,'ltp']
        # put_price=df[df['symbol']==put_name]['ltp'].iloc[0]
        put_price=df.loc[put_name,'ltp']

        print(call_price,put_price)
        condition=paper_option_data_info['condition']

        if ct>end_time:
            print('closing everything')
            
            if call_buy_trade_flag==1:

                paper_option_data_info['call_buy']['quantity']=0
                # call_buy_ltp=df[df['symbol']==call_name]['ltp'].iloc[0]
                call_buy_ltp=df.loc[call_name,'ltp']
                name=paper_option_data_info['call_buy']['option_name']
                a=[name,call_buy_ltp,'SELL',0,0,spot_price,paper_option_data_info['call_buy']['quantity']]
                paper_option_data_info['call_buy']['filled_df'].loc[dt.datetime.now()] = a
                paper_option_data_info['call_buy']['trade_flag']=2

            if put_buy_trade_flag==1:
                paper_option_data_info['put_buy']['quantity']=0
                # put_buy_ltp=df[df['symbol']==put_name]['ltp'].iloc[0]
                put_buy_ltp=df.loc[put_name,'ltp']
                name=paper_option_data_info['put_buy']['option_name']
                a=[name,put_buy_ltp,'SELL',0,0,spot_price,paper_option_data_info['put_buy']['quantity']]

                paper_option_data_info['put_buy']['filled_df'].loc[dt.datetime.now()] = a
                paper_option_data_info['put_buy']['trade_flag']=2

            # return 0
            # sys.exit()

    

        #condition satisfied
        if (pivot-buffer<=spot_price<=pivot+buffer) or (support-buffer<=spot_price <= support+buffer ) or (resistance-buffer <= spot_price <= resistance+buffer) :
            if condition==False:
      
                logging.info('strategy condition condition satisfied')  
                
                call_name=get_otm_option(spot_price, 'CE',0)
                paper_option_data_info['call_buy']['option_name']=call_name
                paper_option_data_info['call_buy']['quantity']=quantity

                put_name=get_otm_option(spot_price, 'PE', 0)
                paper_option_data_info['put_buy']['option_name']=put_name
                paper_option_data_info['put_buy']['quantity']=quantity

                # current_price=df[df['symbol']==call_name]['ltp'].iloc[0]
                current_price=df.loc[call_name,'ltp']
                call_buy_ltp=current_price+profit_loss_point
                call_buy_stop_price=call_buy_ltp-profit_loss_point
                call_buy_profit_price=call_buy_ltp+profit_loss_point

                # current_price=df[df['symbol']==put_name]['ltp'].iloc[0]
                current_price=df.loc[put_name,'ltp']
                put_buy_ltp=current_price+profit_loss_point
                put_buy_stop_price=put_buy_ltp-profit_loss_point
                put_buy_profit_price=put_buy_ltp+profit_loss_point

                paper_option_data_info['call_buy']['buy_price']=call_buy_ltp
                paper_option_data_info['call_buy']['current_stop_price']=call_buy_stop_price
                paper_option_data_info['call_buy']['current_profit_price']=call_buy_profit_price

                paper_option_data_info['put_buy']['buy_price']=put_buy_ltp
                paper_option_data_info['put_buy']['current_stop_price']=put_buy_stop_price
                paper_option_data_info['put_buy']['current_profit_price']=put_buy_profit_price

                paper_option_data_info['condition']=True
                logging.info(f"call price is {call_buy_ltp} and put price is {put_buy_ltp}")
                print('done fetching prices')

        #call buy condition
        if (condition==True) and (call_buy_price<=call_price) and (call_buy_trade_flag==0) :
                a=[call_name,call_price,'BUY',call_buy_stop_price,call_buy_profit_price,spot_price,quantity] 
                paper_option_data_info['call_buy']['filled_df'].loc[ct] = a
                paper_option_data_info['call_buy']['trade_flag']=1
                paper_option_data_info['put_buy']['trade_flag']=3
                logging.info('print done buying')
                print('call buy condition satisfied')


        #call sell condition
        elif condition==True and (call_buy_trade_flag==1) :
        
            if (call_price>call_buy_profit_price) or (call_price<call_buy_stop_price):
                logging.info('sell call condition satisfied')   
                #close position
                name=paper_option_data_info['call_buy']['option_name']
                paper_option_data_info['call_buy']['quantity']=0
                a=[name,call_price,'SELL',0,0,spot_price,0]
                paper_option_data_info['call_buy']['filled_df'].loc[ct] = a
                paper_option_data_info['call_buy']['trade_flag']=2
                print('call sell condition satisfied')


        #put buy condition
        if (condition==True) and (put_buy_price<=put_price) and (put_buy_trade_flag==0) :
            a=[put_name,put_price,'BUY',put_buy_stop_price,put_buy_profit_price,spot_price,quantity]
            paper_option_data_info['put_buy']['filled_df'].loc[ct] = a
            paper_option_data_info['put_buy']['trade_flag']=1
            paper_option_data_info['call_buy']['trade_flag']=3
            logging.info('put buy condition satisfied')
            print('put buy condition satisfied')


        #put sell condition
        elif condition==True and (put_buy_trade_flag==1):
            if (put_price>put_buy_profit_price) or (put_price<put_buy_stop_price):
                logging.info('sell put condition satisfied')
                #close position

                name=paper_option_data_info['put_buy']['option_name']


                paper_option_data_info['put_buy']['quantity']=0
                a=[name,put_price,'SELL',0,0,spot_price,0]
                paper_option_data_info['put_buy']['filled_df'].loc[ct] = a
                paper_option_data_info['put_buy']['trade_flag']=2

                print('put sell condition satisfied')


        #update dataframe
        if not paper_option_data_info['call_buy']['filled_df'].empty:
            paper_option_data_info['call_buy']['filled_df'].to_csv(f'call_buy_{dt.date.today()}.csv')    
        
        if not paper_option_data_info['put_buy']['filled_df'].empty:
            paper_option_data_info['put_buy']['filled_df'].to_csv(f'put_buy_{dt.date.today()}.csv')
  
        store(paper_option_data_info,account_type)

def real_order():
    global quantity
    global live_option_data_info
    global df
    global spot_price
    spot_price=df[df['symbol']==ticker]['ltp'].iloc[0]

    spot_price=df.loc[ticker,'ltp']
    print(f"spot is {spot_price} pivot is {pivot} support is {support} resistance is {resistance}")
    print(spot_price)
    ct=dt.datetime.now()
    if ct>start_time:

        # print(df)
        call_buy_trade_flag=live_option_data_info['call_buy']['trade_flag']
        put_buy_trade_flag=live_option_data_info['put_buy']['trade_flag']

        call_buy_stop_price=live_option_data_info['call_buy']['current_stop_price']
        put_buy_stop_price=live_option_data_info['put_buy']['current_stop_price']

        call_buy_profit_price=live_option_data_info['call_buy']['current_profit_price']
        put_buy_profit_price=live_option_data_info['put_buy']['current_profit_price']
        
        call_name=live_option_data_info['call_buy']['option_name']
        put_name=live_option_data_info['put_buy']['option_name']

        call_buy_price=live_option_data_info['call_buy']['buy_price']
        put_buy_price=live_option_data_info['put_buy']['buy_price']
        # print(call_name, put_name)
        # call_price=df[df['symbol']==call_name]['ltp'].iloc[0]
        call_price=df.loc[call_name,'ltp']
        # put_price=df[df['symbol']==put_name]['ltp'].iloc[0]
        put_price=df.loc[put_name,'ltp']

        print(call_price,put_price)
        condition=live_option_data_info['condition']

        if ct>end_time:
            print('closing everything')
            
            if call_buy_trade_flag==1:
                name=live_option_data_info['call_buy']['option_name']
                data = {"id":name+"-INTRADAY"}
                response = fyers.exit_positions(data=data)
                print(response)

                if response['s']=='ok':

                    live_option_data_info['call_buy']['quantity']=0
                    # call_buy_ltp=df[df['symbol']==call_name]['ltp'].iloc[0]
                    call_buy_ltp=df.loc[name,'ltp']
                    
                    a=[name,call_buy_ltp,'SELL',0,0,spot_price,live_option_data_info['call_buy']['quantity']]
                    live_option_data_info['call_buy']['filled_df'].loc[dt.datetime.now()] = a
                    live_option_data_info['call_buy']['trade_flag']=2

            if put_buy_trade_flag==1:
                name=live_option_data_info['put_buy']['option_name']
                data = {"id":name+"-INTRADAY"}
                response = fyers.exit_positions(data=data)
                print(response)

                if response['s']=='ok':
                    live_option_data_info['put_buy']['quantity']=0
                    # put_buy_ltp=df[df['symbol']==put_name]['ltp'].iloc[0]
                    put_buy_ltp=df.loc[put_name,'ltp']
            
                    a=[name,put_buy_ltp,'SELL',0,0,spot_price,live_option_data_info['put_buy']['quantity']]
                    live_option_data_info['put_buy']['filled_df'].loc[dt.datetime.now()] = a
                    live_option_data_info['put_buy']['trade_flag']=2

            

        #condition satisfied
        if (pivot-buffer<=spot_price<=pivot+buffer) or (support-buffer<=spot_price <= support+buffer ) or (resistance-buffer <= spot_price <= resistance+buffer) :
            if condition==False:
      
                logging.info('strategy condition condition satisfied')  
                
                call_name=get_otm_option(spot_price, 'CE',0)
                live_option_data_info['call_buy']['option_name']=call_name
                live_option_data_info['call_buy']['quantity']=quantity

                put_name=get_otm_option(spot_price, 'PE', 0)
                live_option_data_info['put_buy']['option_name']=put_name
                live_option_data_info['put_buy']['quantity']=quantity

                # current_price=df[df['symbol']==call_name]['ltp'].iloc[0]
                current_price=df.loc[call_name,'ltp']
                call_buy_ltp=current_price+profit_loss_point
                call_buy_stop_price=call_buy_ltp-profit_loss_point
                call_buy_profit_price=call_buy_ltp+profit_loss_point

                # current_price=df[df['symbol']==put_name]['ltp'].iloc[0]
                current_price=df.loc[put_name,'ltp']
                put_buy_ltp=current_price+profit_loss_point
                put_buy_stop_price=put_buy_ltp-profit_loss_point
                put_buy_profit_price=put_buy_ltp+profit_loss_point

                live_option_data_info['call_buy']['buy_price']=call_buy_ltp
                live_option_data_info['call_buy']['current_stop_price']=call_buy_stop_price
                live_option_data_info['call_buy']['current_profit_price']=call_buy_profit_price

                live_option_data_info['put_buy']['buy_price']=put_buy_ltp
                live_option_data_info['put_buy']['current_stop_price']=put_buy_stop_price
                live_option_data_info['put_buy']['current_profit_price']=put_buy_profit_price

                live_option_data_info['condition']=True
                logging.info(f"call price is {call_buy_ltp} and put price is {put_buy_ltp}")
                print('done fetching prices')

        #call buy condition
        if (condition==True) and (call_buy_price<=call_price) and (call_buy_trade_flag==0) :
            data = {
                "symbol":live_option_data_info['call_buy']['option_name'],
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
                a=[call_name,call_price,'BUY',call_buy_stop_price,call_buy_profit_price,spot_price,quantity] 
                live_option_data_info['call_buy']['filled_df'].loc[ct] = a
                live_option_data_info['call_buy']['trade_flag']=1
                live_option_data_info['put_buy']['trade_flag']=3
                logging.info('print done buying')
                print('call buy condition satisfied')


        #call sell condition
        elif condition==True and (call_buy_trade_flag==1) :
        
            if (call_price>call_buy_profit_price) or (call_price<call_buy_stop_price):
                logging.info('sell call condition satisfied')   
                #close position
                name=live_option_data_info['call_buy']['option_name']
                data = {"id":name+"-INTRADAY"}
                response = fyers.exit_positions(data=data)
                print(response)

                if response['s']=='ok':


                    live_option_data_info['call_buy']['quantity']=0
                    a=[name,call_price,'SELL',0,0,spot_price,0]
                    live_option_data_info['call_buy']['filled_df'].loc[ct] = a
                    live_option_data_info['call_buy']['trade_flag']=2
                    print('call sell condition satisfied')


        #put buy condition
        if (condition==True) and (put_buy_price<=put_price) and (put_buy_trade_flag==0) :

            data = {
                "symbol":live_option_data_info['put_buy']['option_name'],
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

                a=[put_name,put_price,'BUY',put_buy_stop_price,put_buy_profit_price,spot_price,quantity]
                live_option_data_info['put_buy']['filled_df'].loc[ct] = a
                live_option_data_info['put_buy']['trade_flag']=1
                live_option_data_info['call_buy']['trade_flag']=3
                logging.info('put buy condition satisfied')
                print('put buy condition satisfied')


        #put sell condition
        elif condition==True and (put_buy_trade_flag==1):
            if (put_price>put_buy_profit_price) or (put_price<put_buy_stop_price):
                logging.info('sell put condition satisfied')
                #close position

                name=live_option_data_info['put_buy']['option_name']
                data = {"id":name+"-INTRADAY"}
                response = fyers.exit_positions(data=data)
                print(response)

                if response['s']=='ok':
                    live_option_data_info['put_buy']['quantity']=0
                    a=[name,put_price,'SELL',0,0,spot_price,0]
                    live_option_data_info['put_buy']['filled_df'].loc[ct] = a
                    live_option_data_info['put_buy']['trade_flag']=2
                    print('put sell condition satisfied')


        #update dataframe
        if not live_option_data_info['call_buy']['filled_df'].empty:
            live_option_data_info['call_buy']['filled_df'].to_csv(f'call_buy_{dt.date.today()}.csv')    
        
        if not live_option_data_info['put_buy']['filled_df'].empty:
            live_option_data_info['put_buy']['filled_df'].to_csv(f'put_buy_{dt.date.today()}.csv')
  
        store(live_option_data_info,account_type)





time.sleep(3)

async def main_strategy_code():
    global df
    
    while True:
        #getting oi data every minute
        ct=dt.datetime.now()
        if df.shape[0]!=0:
            print(ct)
            # df.to_csv('real_time_data.csv')
            if account_type=='PAPER':
                paper_order()
            else:
                real_order()

        await asyncio.sleep(1)


async def main():
    while True:
        await main_strategy_code()

asyncio.run(main())
