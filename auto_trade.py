import os
import pandas as pd
import time
from datetime import datetime
from argparse import ArgumentParser
from binance import Client
from binance.exceptions import BinanceAPIException

def get_account_info(client):
    info = client.get_account()
    print(info)
    
def get_withdraw_history(client):
    withdraws = client.get_withdraw_history()
    print(withdraws)
    
def get_futures_balance(client):
    balance = client.futures_account_balance()
    balance_df = pd.DataFrame(balance)
    
    usdt_balance = float(balance_df[balance_df['asset']=='USDT']['balance'].iloc[0])
    btc_balance = float(balance_df[balance_df['asset']=='BTC']['balance'].iloc[0])
    print(f'usdt_balance: {usdt_balance} / btc_balance: {btc_balance}')
    
def get_all_orders(client, status=None):
    orders = client.futures_get_all_orders(symbol='BTCUSDT')
    orders_df = pd.DataFrame(orders)
    if status is None:
        print(orders_df[['time','updateTime','avgPrice','origQty','side','positionSide','status','stopPrice']])
    else:
        print(orders_df[orders_df['status']==status][['time','updateTime','avgPrice','origQty','side','positionSide','status','stopPrice']])   

def futures_change_leverage(client, leverage):
    leverage_change = client.futures_change_leverage(symbol='BTCUSDT',
                                                     leverage=leverage)
    print(leverage_change)
    
def get_max_order_info(client, leverage, fee_rate=0.0005):
    balance = client.futures_account_balance()
    balance_df = pd.DataFrame(balance)
    usdt_balance = float(balance_df[balance_df['asset']=='USDT']['balance'].iloc[0])
    
    mark_price = float(client.futures_mark_price(symbol='BTCUSDT')['markPrice'])
    max_quantity = round(usdt_balance/(mark_price*(1+fee_rate)), 4) * leverage * 0.99
    return mark_price, max_quantity

def create_futures_order(client, order_position, mark_price, max_quantity):
    if order_position == 'LONG':
        take_profit_price = mark_price * 1.005
        stop_loss_price = mark_price * 0.995
    elif order_position == 'SHORT':
        take_profit_price = mark_price * 0.995
        stop_loss_price = mark_price * 1.005      
    
    buy_order = client.futures_create_order(symbol='BTCUSDT',
                                            side='BUY',
                                            positionSide=order_position,
                                            type='MARKET',
                                            quantity=max_quantity)

    take_profit_market = client.futures_create_order(symbol='BTCUSDT',
                                                     side='SELL',
                                                     positionSide=order_position,
                                                     type='TAKE_PROFIT_MARKET',
                                                     timeInForce='GTC',
                                                     quantity=max_quantity,
                                                     price=take_profit_price,
                                                     stopPrice=take_profit_price,
                                                     closePosition=True)

    stop_market = client.futures_create_order(symbol='BTCUSDT',
                                              side='SELL',
                                              positionSide=order_position,
                                              type='STOP_MARKET',
                                              timeInForce='GTC',
                                              quantity=max_quantity,
                                              price=stop_loss_price,
                                              stopPrice=stop_loss_price,
                                              closePosition=True)
    
def main(args):
    with open(os.path.join(args.key_path, 'public.txt'), 'r') as f:
        for line in f.readlines():
            api_key = line
            break
    with open(os.path.join(args.key_path, 'secret.txt'), 'r') as f:
        for line in f.readlines():
            api_secret = line
            break
    
    client = Client(api_key, api_secret)
    futures_change_leverage(client, 10)
    
    while True:
        if int(datetime.now().second) == 0:
            klines = client.futures_klines(symbol='BTCUSDT', interval='1m', limit=args.kline_limit)    
            up_down = [float(kline[4])>float(kline[1]) for kline in klines[-args.check_window_len-1:-1]]
            
            close = [float(kline[4]) for kline in klines]
            ma_7 = [sum(close[i-6:i+1])/7 for i in range(args.kline_limit - args.check_window_len - 1, args.kline_limit-1)]
            ma_25 = [sum(close[i-24:i+1])/25 for i in range(args.kline_limit - args.check_window_len - 1, args.kline_limit-1)]
            ma_99 = [sum(close[i-98:i+1])/99 for i in range(args.kline_limit - args.check_window_len - 1, args.kline_limit-1)]
            
            if sum(up_down) == args.check_window_len:
                ma25_pos = [ma_7[i]<ma_25[i] for i in range(args.check_window_len)]
                ma99_pos = [ma_7[i]<ma_99[i] for i in range(args.check_window_len)]
                if sum(ma25_pos) == args.check_window_len and sum(ma99_pos) == args.check_window_len:
                    ma25_change = [ma_25[i+1]-ma_25[i] >= -args.change_threshold for i in range(args.check_window_len-1)]
                    ma99_change = [ma_99[i+1]-ma_99[i] >= -args.change_threshold for i in range(args.check_window_len-1)]
                    if sum(ma25_change) == args.check_window_len-1 and sum(ma99_change) == args.check_window_len-1:
                        mark_price, max_quantity = get_max_order_info(client, leverage=args.leverage, fee_rate=0.0005)
                        try:
                            create_futures_order(client, order_position="LONG", mark_price=mark_price, max_quantity=max_quantity)
                        except BinanceAPIException as e:
                            print(e)
                        else:
                            print("LONG order Success")
                        
            elif sum(up_down) == 0:
                ma25_pos = [ma_7[i]>ma_25[i] for i in range(args.check_window_len)]
                ma99_pos = [ma_7[i]>ma_99[i] for i in range(args.check_window_len)]
                if sum(ma25_pos) == args.check_window_len and sum(ma99_pos) == args.check_window_len:
                    ma25_change = [ma_25[i+1]-ma_25[i] <= args.change_threshold for i in range(args.check_window_len-1)]
                    ma99_change = [ma_99[i+1]-ma_99[i] <= args.change_threshold for i in range(args.check_window_len-1)]
                    if sum(ma25_change) == args.check_window_len-1 and sum(ma99_change) == args.check_window_len-1:
                        mark_price, max_quantity = get_max_order_info(client, leverage=args.leverage, fee_rate=0.0005)
                        try:
                            create_futures_order(client, order_position="SHORT", mark_price=mark_price, max_quantity=max_quantity)
                        except BinanceAPIException as e:
                            print(e)
                        else:
                            print("SHORT order Success")
            
            else:
                print("Not a good timing for entering")
                time.sleep(59)
    

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--key_path', type=str, default='./keys')
    parser.add_argument('--leverage', type=int, default=10)
    parser.add_argument('--kline_limit', type=int, default=110)
    parser.add_argument('--check_window_len', type=int, default=3)
    parser.add_argument('--change_threshold', type=float, default=3)
    args = parser.parse_args()
    main(args)