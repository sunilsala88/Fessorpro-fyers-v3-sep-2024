# Sell 100 pts away BN Strangle at 9:30
# Initial Sl at 25% of premium of corresponding leg
# For every 25% profit trail Sl by 25%
# Max 15:20
# credit aritra


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
logging.basicConfig(level=logging.INFO, filename=f'option_strategy_{dt.date.today()}.log',filemode='a',format="%(asctime)s - %(message)s")

index_name='NIFTYBANK'
ticker=f"NSE:{index_name}-INDEX"
# ticker='MCX:CRUDEOIL24DECFUT'
strike_count=10
strike_diff=100
account_type='PAPER'


start_hour,start_min=9,35
end_hour,end_min=20,5
quantity=15

stop_perc=25
sell_points=100


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
    print(option_chain)
    print(otm_strike)
    otm_option=option_chain[(option_chain['strike_price']==otm_strike) & (option_chain['option_type']==side) ]['symbol'].squeeze()
    return otm_option,otm_strike


position_df=get_position()
order_df=get_order()    

print(position_df)
print(order_df)


sell_call_option,call_sell_strike=get_otm_option(option_chain['ltp'].iloc[0], 'CE',sell_points)
sell_put_option,put_sell_strike=get_otm_option(option_chain['ltp'].iloc[0], 'PE',sell_points)
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
                                'call_sell':{'name':sell_call_option,'flag':0,'sell_price':0,'stop_price':0,'profit_price':0,'filled_df':filled_df.copy(),'spot':0,'quantity':0,'strike':0,'p_constant':0,'sl_constant':0,'sl_diff':0},
                                'put_sell':{'name':sell_put_option,'flag':0,'sell_price':0,'stop_price':0,'profit_price':0,'filled_df':filled_df.copy(),'spot':0,'quantity':0,'strike':0,'p_constant':0,'sl_constant':0,'sl_diff':0},
                                "main_flag":0,
                                'enter_spot_price':0,
                                'initial_spot_price':0,
                                'filled_df':filled_df,
                                'condition':False
                                }

        
else:
    try:
        live_option_data_info=load(account_type)

    except:
        column_names = ['time','ticker','price','action','stop_price','take_profit','spot_price','quantity']
        filled_df = pd.DataFrame(columns=column_names)
        filled_df.set_index('time',inplace=True)
        live_option_data_info={
                                'call_sell':{'name':sell_call_option,'flag':0,'sell_price':0,'stop_price':0,'profit_price':0,'filled_df':filled_df.copy(),'spot':0,'quantity':0,'strike':0,'p_constant':0,'sl_constant':0,'sl_diff':0},
                                'put_sell':{'name':sell_put_option,'flag':0,'sell_price':0,'stop_price':0,'profit_price':0,'filled_df':filled_df.copy(),'spot':0,'quantity':0,'strike':0,'p_constant':0,'sl_constant':0,'sl_diff':0},
                                "main_flag":0,
                                'enter_spot_price':0,
                                'initial_spot_price':0,
                                'filled_df':filled_df,
                                'condition':False
                                }



logging.info('started')



def paper_order():
    global quantity
    global paper_option_data_info
    global df
    global spot_price
    #get spot price

    spot_price=df.loc[ticker,'ltp']
    #current time
    ct=dt.datetime.now()
    # print(df)
    
    #if current time is greater than current time than start strategy
    if ct>start_time:

        #get flag
        call_sell_trade_flag=paper_option_data_info['call_sell']['flag']
        put_sell_trade_flag=paper_option_data_info['put_sell']['flag']

        #get stop price
        call_sell_stop_price=paper_option_data_info['call_sell']['stop_price']
        put_sell_stop_price=paper_option_data_info['put_sell']['stop_price']
        
        #get name
        call_sell_name=paper_option_data_info['call_sell']['name']
        put_sell_name=paper_option_data_info['put_sell']['name']
        print(call_sell_name,put_sell_name)

        #get buy price
        call_sell_price=paper_option_data_info['call_sell']['sell_price']
        put_sell_price=paper_option_data_info['put_sell']['sell_price']

        #get current price
        call_sell_current_price=df.loc[call_sell_name,'ltp']
        put_sell_current_price=df.loc[put_sell_name,'ltp']

        #get condition
        condition=paper_option_data_info['condition']
        print(call_sell_current_price,put_sell_current_price)
        print(f" call sell price {call_sell_price}  put sell price {put_sell_price}")
        print(f" call sell stop price {call_sell_stop_price}  put sell stop price {put_sell_stop_price}")
        # logging.info(f"call current price {call_sell_current_price} put current price {put_sell_current_price}")

        #if current time is greater than end time
        if ct>end_time:
            print('closing everything')
            
            if call_sell_trade_flag==1:
                #close call buy position
                paper_option_data_info['call_sell']['quantity']=0 #change quantity
                a=[call_sell_name,call_sell_current_price,'BUY',0,0,spot_price,paper_option_data_info['call_sell']['quantity']]
                paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a #update dataframe
                paper_option_data_info['call_sell']['flag']=5 #change flag so no trade taken again
                logging.info('closing call leg due to time condition') 


            if put_sell_trade_flag==1:
                #close call put position
                paper_option_data_info['put_sell']['quantity']=0 #change quantity
                a=[put_sell_name,put_sell_current_price,'BUY',0,0,spot_price,paper_option_data_info['put_sell']['quantity']]
                paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a #update dataframe
                paper_option_data_info['put_sell']['flag']=5 #change flag so no trade taken again
                logging.info('closing put leg due to time condition') 


        if condition==False:
      
            logging.info('strategy condition condition satisfied')  

            call_sell_name,strike=get_otm_option(spot_price, 'CE',sell_points) #get call name
            paper_option_data_info['call_sell']['name']=call_sell_name #update call name data
            paper_option_data_info['call_sell']['quantity']=quantity #update quantity
            paper_option_data_info['call_sell']['flag']=1

            put_sell_name,strike=get_otm_option(spot_price, 'PE', sell_points) #get put name
            paper_option_data_info['put_sell']['name']=put_sell_name #update put name
            paper_option_data_info['put_sell']['quantity']=quantity #update put quantity
            paper_option_data_info['put_sell']['flag']=1


            paper_option_data_info['call_sell']['sell_price']=call_sell_current_price #save call buy price
            paper_option_data_info['call_sell']['stop_price']=call_sell_current_price*(1+(stop_perc/100)) #save call stop price

     

            paper_option_data_info['put_sell']['sell_price']=put_sell_current_price #save put buy price
            paper_option_data_info['put_sell']['stop_price']=put_sell_current_price*(1+(stop_perc/100)) #save put stop price



            a=[call_sell_name,call_sell_current_price,'SELL',call_sell_current_price*(1+(stop_perc/100)),0,spot_price,paper_option_data_info['call_sell']['quantity']]
            paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a

            a=[put_sell_name,put_sell_current_price,'SELL',put_sell_current_price*(1+(stop_perc/100)),0,spot_price,paper_option_data_info['put_sell']['quantity']]
            paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a

            paper_option_data_info['condition']=True #update condition
            logging.info('selling call and put')
            # logging.info(f"call price is {call_sell_current_price} and put price is {put_sell_current_price}")
            # logging.info(f"call stop price is {call_sell_current_price*(1+initial_stop_loss)} and put stop price is {put_sell_current_price*(1+initial_stop_loss)}")
            print('done fetching prices')
        
        else:
            print('we have posiiton')

            #trailing
            if call_sell_trade_flag==1:
                
                if call_sell_current_price>call_sell_stop_price:
                    logging.info(f"call current price {call_sell_current_price} put current price {put_sell_current_price}")

                    #stop price breached
                    paper_option_data_info['call_sell']['quantity']=0 #change quantity
                    a=[call_sell_name,call_sell_current_price,'BUY',0,0,spot_price,paper_option_data_info['call_sell']['quantity']]
                    paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a #update dataframe
                    paper_option_data_info['call_sell']['flag']=5 #change flag so no trade taken again
                    logging.info('closing call leg due to stop price condition') 
                    

                else:
                    #update stop price
                    call_sell_price=paper_option_data_info['call_sell']['sell_price']
                    call_last_price=df.loc[call_sell_name,'ltp']
                    call_stop_price=paper_option_data_info['call_sell']['stop_price']
                    if call_last_price<call_stop_price-((stop_perc/100)*call_sell_price*2):
                        logging.info(f'updating stop price , current_stop is {call_stop_price} new stop is {call_stop_price-((stop_perc/100)*call_sell_price)} current price is {call_last_price}')
                        
                        call_new_stop_price=call_stop_price-((stop_perc/100)*call_sell_price)
                        paper_option_data_info['call_sell']['stop_price']=call_new_stop_price
                        a=[call_sell_name,call_last_price,'TRAIL',call_new_stop_price,0,spot_price,paper_option_data_info['call_sell']['quantity']]
                        paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a



            if put_sell_trade_flag == 1:
                if put_sell_current_price>put_sell_stop_price:
                    logging.info(f"call current price {call_sell_current_price} put current price {put_sell_current_price}")
                    #stop price breached
                    paper_option_data_info['put_sell']['quantity']=0 #change quantity
                    a=[put_sell_name,put_sell_current_price,'BUY',0,0,spot_price,paper_option_data_info['put_sell']['quantity']]
                    paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a #update dataframe
                    paper_option_data_info['put_sell']['flag']=5 #change flag so no trade taken again
                    logging.info('closing put leg due to stop price condition')

                else:
                    #update stop price
                    put_sell_price=paper_option_data_info['put_sell']['sell_price']
                    put_last_price=df.loc[put_sell_name,'ltp']
                    put_stop_price=paper_option_data_info['put_sell']['stop_price']
                    if put_last_price<put_stop_price-((stop_perc/100)*put_sell_price*2):
                        logging.info(f'updating stop price, current_stop is {put_stop_price} new stop is {put_stop_price-((stop_perc/100)*put_sell_price)} current price is {put_last_price}')
                        put_new_stop_price=put_stop_price-((stop_perc/100)*put_sell_price)
                        paper_option_data_info['put_sell']['stop_price']=put_new_stop_price
                        a=[put_sell_name,put_last_price,'TRAIL',put_new_stop_price,0,spot_price,paper_option_data_info['put_sell']['quantity']]
                        paper_option_data_info['filled_df'].loc[dt.datetime.now()] = a

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
