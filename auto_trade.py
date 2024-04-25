import os
import time
from datetime import datetime
from argparse import ArgumentParser
from binance import Client
from binance.exceptions import BinanceAPIException
from account import futures_change_leverage, get_max_order_info
from trade_signal import get_momentum_signal, get_arbitrage_signal

def create_futures_order(client, order_position, stop_threshold, mark_price, max_quantity):
    if order_position == 'LONG':
        take_profit_price = mark_price * (1+stop_threshold)
        stop_loss_price = mark_price * (1-stop_threshold)
    elif order_position == 'SHORT':
        take_profit_price = mark_price * (1-stop_threshold)
        stop_loss_price = mark_price * (1+stop_threshold)
    
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
    
    print(buy_order)
    print(take_profit_market)
    print(stop_market)
    
    
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
            position = get_momentum_signal(klines, args.kline_limit, args.check_window_len, args.change_threshold)
            
            if position in ["LONG", "SHORT"]:
                mark_price, max_quantity = get_max_order_info(client, leverage=args.leverage, max_ratio=args.max_ratio)
                try:
                    create_futures_order(client, order_position=position, stop_threshold = args.stop_threshold,
                                         mark_price=mark_price, max_quantity=max_quantity)
                except BinanceAPIException as e:
                    print(e)
                else:
                    print(f"{position} order Success")
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
    parser.add_argument('--stop_threshold', type=float, default=0.005)
    parser.add_argument('--max_ratio', type=float, default=0.99)
    args = parser.parse_args()
    main(args)