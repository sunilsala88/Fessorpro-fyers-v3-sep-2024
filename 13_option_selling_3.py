#strategy description:
#open range option selling strategy
#1. wait till 10:15 and calculate high and low from 9:15 to 10:15
#2. sell atm call and put option at 10:15
#3. if spot price goes above high, buy atm call option (closing loss making call position )
#4. if spot price goes below low, buy atm put option (closing loss making put position )
#5. after closing call position if spot price comes below high, sell atm call option again
#6. after closing  put position if spot price comes above low, sell atm put option again
#7. if the spot price is between high and low, do nothing
#8. checking for condition every 5 minutes
#9. closing all positions at 15:25




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
logging.basicConfig(level=logging.INFO, filename=f'option_strategy_{dt.date.today()}',filemode='a',format="%(asctime)s - %(message)s")

index_name='NIFTY50'
ticker=f"NSE:{index_name}-INDEX"
# ticker='MCX:CRUDEOIL24DECFUT'
strike_count=10
strike_diff=50
account_type='PAPER'

buffer_level=20
# profit_loss_point=30
start_hour,start_min=9,35
end_hour,end_min=15,5
quantity=25




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
    print(option_chain)
    print(otm_strike)
    otm_option=option_chain[(option_chain['strike_price']==otm_strike) & (option_chain['option_type']==side) ]['symbol'].squeeze()
    return otm_option,otm_strike


position_df=get_position()
order_df=get_order()    

print(position_df)
print(order_df)


sell_call_option,call_sell_strike=get_otm_option(option_chain['ltp'].iloc[0], 'CE',0)
sell_put_option,put_sell_strike=get_otm_option(option_chain['ltp'].iloc[0], 'PE',0)
print(sell_call_option,sell_put_option)



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
        paper_option_data_info={
                                'call_sell':{'name':sell_call_option,'flag':0,'sell_price':0,'stop_price':0,'profit_price':0,'filled_df':filled_df.copy(),'spot':0,'quantity':0,'strike':0,'max_pos':0},
                                'put_sell':{'name':sell_put_option,'flag':0,'sell_price':0,'stop_price':0,'profit_price':0,'filled_df':filled_df.copy(),'spot':0,'quantity':0,'strike':0,'max_pos':0},

                                "main_flag":0,
                                'enter_spot_price':0,
                                'initial_spot_price':0,
                                'filled_df':filled_df,
                                'high':0,
                                'low':0
                                }

        
else:
    try:
        live_option_data_info=load(account_type)

    except:
        column_names = ['time','ticker','price','action','stop_price','take_profit','spot_price','quantity']
        filled_df = pd.DataFrame(columns=column_names)
        filled_df.set_index('time',inplace=True)
        live_option_data_info={
                                'call_sell':{'name':sell_call_option,'flag':0,'sell_price':0,'stop_price':0,'profit_price':0,'filled_df':filled_df.copy(),'spot':0,'quantity':0,'strike':0,'max_pos':0},
                                'put_sell':{'name':sell_put_option,'flag':0,'sell_price':0,'stop_price':0,'profit_price':0,'filled_df':filled_df.copy(),'spot':0,'quantity':0,'strike':0,'max_pos':0},

                                "main_flag":0,
                                'enter_spot_price':0,
                                'initial_spot_price':0,
                                'filled_df':filled_df,
                                'high':0,
                                'low':0
                                }

logging.info('started')


def get_levels():
        """
        Fetch historical data, calculate RSI, and update it to Excel every 30 minutes.
        """
        f = dt.date.today() - dt.timedelta(60)
        p = dt.date.today()
        data = {
            "symbol": ticker,
            "resolution": "5",
            "date_format": "1",
            "range_from": f.strftime('%Y-%m-%d'),
            "range_to": p.strftime('%Y-%m-%d'),
            "cont_flag": "1"
        }


        # Fetch historical data
        response2 =fyers.history(data=data)
        historical_data1 = pd.DataFrame(response2['candles'])
        historical_data1.columns = ['date', 'open', 'high', 'low', 'close', 'volume']

        # Convert date to IST
        ist = pytz.timezone('Asia/Kolkata')
        historical_data1['date'] = pd.to_datetime(historical_data1['date'], unit='s').dt.tz_localize('UTC').dt.tz_convert(ist)
        #historical_data1.reset_index(inplace=True, drop=True)
        historical_data1=historical_data1[historical_data1['date'].dt.date==dt.datetime.now().date()]
        print(historical_data1)
        historical_data1=historical_data1[historical_data1['date'].dt.time<dt.datetime(2024,12,6,10,15).time()]
        return historical_data1['high'].max(), historical_data1['low'].min()
       

h,l=get_levels()
print(h,l)


def paper_order():
    global quantity
    global paper_option_data_info
    global df
    global spot_price
    # spot_price=df[df['symbol']==ticker]['ltp'].iloc[0]
    spot_price=df.loc[ticker,'ltp']
    print(f"spot is {spot_price} ")
    ct=dt.datetime.now()
    # print(df)
    if ct>start_time:

        #name
        call_sell_name=paper_option_data_info.get('call_sell').get('name')
        put_sell_name=paper_option_data_info.get('put_sell').get('name')

        #flag
        
        call_sell_flag=paper_option_data_info.get('call_sell').get('flag')
        put_sell_flag=paper_option_data_info.get('put_sell').get('flag')

        #buy_price
     
        call_sell_price=paper_option_data_info.get('call_sell').get('sell_price')
        put_sell_price=paper_option_data_info.get('put_sell').get('sell_price')

 
        call_sell_current_price=df.loc[call_sell_name,'ltp']
        put_sell_current_price=df.loc[put_sell_name,'ltp']

        main_flag=paper_option_data_info['main_flag']
        enter_spot_price=paper_option_data_info['enter_spot_price']
        print("main flag",main_flag,enter_spot_price)
        print(paper_option_data_info['low'],paper_option_data_info['high'])
        print(call_sell_name,put_sell_name)

        if ct>end_time:
            print('closing everything')
            #close call buy

            
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
            logging.info('placing short straddle ')  
            paper_option_data_info['high'],paper_option_data_info['low']=get_levels()
            # paper_option_data_info['high'],paper_option_data_info['low']=51800,51600
            #selling legs
            call_sell_name,strike=get_otm_option(spot_price, 'CE', 0)
            paper_option_data_info['call_sell']['name']=call_sell_name
            paper_option_data_info['call_sell']['quantity']=quantity
            paper_option_data_info['call_sell']['strike']=strike
            paper_option_data_info['call_sell']['max_pos']=1

            put_sell_name,strike=get_otm_option(spot_price, 'PE', 0)
            paper_option_data_info['put_sell']['name']=put_sell_name
            paper_option_data_info['put_sell']['quantity']=quantity
            paper_option_data_info['put_sell']['strike']=strike
            paper_option_data_info['put_sell']['max_pos']=1

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
          
            if spot_price > paper_option_data_info['high'] and paper_option_data_info['call_sell']['flag']==1 and paper_option_data_info['call_sell']['max_pos']<3:
                #spot price has breached high
                #close call sell leg
                paper_option_data_info['call_sell']['quantity']=0
                a=[call_sell_name,call_sell_current_price,'BUY',0,0,spot_price,paper_option_data_info['call_sell']['quantity']] 
                paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                paper_option_data_info['call_sell']['flag']=2
                time.sleep(1)
                paper_option_data_info['enter_spot_price']=spot_price
                paper_option_data_info['main_flag']=2
                print('done doing adjustment')
        
            elif spot_price< paper_option_data_info['low'] and paper_option_data_info['put_sell']['flag']==1 and paper_option_data_info['put_sell']['max_pos']<3:
                #spot price has breached low
                #close put sell leg
                paper_option_data_info['put_sell']['quantity']=0
                a=[put_sell_name,put_sell_current_price,'BUY',0,0,spot_price,paper_option_data_info['put_sell']['quantity']]
                paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                paper_option_data_info['put_sell']['flag']=2
                time.sleep(1)
                paper_option_data_info['enter_spot_price']=spot_price
                paper_option_data_info['main_flag']=2
                print('done doing adjustment')    


        elif (main_flag==2):
            if (paper_option_data_info['call_sell']['flag']==2) and (spot_price < (paper_option_data_info['high']-buffer_level)) and paper_option_data_info['call_sell']['max_pos']<3:
                    print('open call leg again')
                    paper_option_data_info['call_sell']['quantity']=quantity
                    a=[call_sell_name,call_sell_current_price,'SELL',0,0,spot_price,paper_option_data_info['call_sell']['quantity']]
                    paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                    paper_option_data_info['call_sell']['flag']=1
                    paper_option_data_info['enter_spot_price']=spot_price
                    paper_option_data_info['main_flag']=1
                    paper_option_data_info['call_sell']['max_pos']+=1
                    print('done doing adjustment')
            
            elif (paper_option_data_info['put_sell']['flag']==2) and (spot_price > (paper_option_data_info['low']+buffer_level)) and paper_option_data_info['put_sell']['max_pos']<3:
                    print('open put leg again')
                    paper_option_data_info['put_sell']['quantity']=quantity
                    a=[put_sell_name,put_sell_current_price,'SELL',0,0,spot_price,paper_option_data_info['put_sell']['quantity']]
                    paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a
                    paper_option_data_info['put_sell']['flag']=1
                    paper_option_data_info['enter_spot_price']=spot_price
                    paper_option_data_info['main_flag']=1
                    paper_option_data_info['put_sell']['max_pos']+=1
                    print('done doing adjustment')



        #update dataframe
        if not paper_option_data_info['filled_df'].empty:
            paper_option_data_info['filled_df'].to_csv(f'trades_{dt.date.today()}.csv')    
        

        store(paper_option_data_info,account_type)



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
