import os
import time
from datetime import datetime
from argparse import ArgumentParser
from binance import Client
from binance.exceptions import BinanceAPIException
from account import futures_change_leverage, get_max_order_info
# from trade_signal import get_momentum_signal, get_arbitrage_signal
from real_time_predict import predict

def create_futures_order(client, order_position, order_wait_sec, tp_threshold, sl_threshold, mark_price, max_quantity):
    if order_position == 'LONG':
        take_profit_price = mark_price * (1+tp_threshold)
        stop_loss_price = mark_price * (1-sl_threshold)
    elif order_position == 'SHORT':
        take_profit_price = mark_price * (1-tp_threshold)
        stop_loss_price = mark_price * (1+sl_threshold)
    
    curr_timestamp = int(time.time()*1000)
    buy_order = client.futures_create_order(symbol='BTCUSDT',
                                            side='BUY',
                                            positionSide=order_position,
                                            type='LIMIT',
                                            timeInForce='GTD',
                                            price=mark_price,
                                            quantity=max_quantity,
                                            goodTillDate=curr_timestamp+order_wait_sec*1000)

    take_profit_order = client.futures_create_order(symbol='BTCUSDT',
                                                    side='SELL',
                                                    positionSide=order_position,
                                                    type='TAKE_PROFIT',
                                                    timeInForce='GTC',
                                                    stopPrice=mark_price,
                                                    price=take_profit_price,
                                                    quantity=max_quantity,
                                                    closePosition=True)
    
    stop_market = client.futures_create_order(symbol='BTCUSDT',
                                              side='SELL',
                                              positionSide=order_position,
                                              type='STOP',
                                              timeInForce='GTC',
                                              stopPrice=mark_price,
                                              price=stop_loss_price,
                                              quantity=max_quantity,
                                              closePosition=True)
    
    print(buy_order)
    print(take_profit_order)
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
    futures_change_leverage(client, args.leverage)
    
    while True:
        if int(datetime.now().second) == 5:
            # klines = client.futures_klines(symbol='BTCUSDT', interval='1m', limit=args.kline_limit)    
            # position = get_momentum_signal(klines, args.kline_limit, args.check_window_len, args.change_threshold)
            pred = predict(client, args)
            if pred >= args.strong_threshold:
                position = "LONG"
            elif pred <= -args.strong_threshold:
                position = "SHORT"
            
            if position in ["LONG", "SHORT"]:
                mark_price, max_quantity = get_max_order_info(client, leverage=args.leverage, max_ratio=args.max_ratio)
                try:
                    create_futures_order(client, order_position=position, order_wait_sec = args.order_wait_sec,
                                         tp_threshold = args.tp_threshold, sl_threshold = args.sl_threshold,
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
    parser.add_argument('--order_wait_sec', type=float, default=50)
    parser.add_argument('--tp_threshold', type=float, default=0.001)
    parser.add_argument('--sl_threshold', type=float, default=0.005)
    parser.add_argument('--max_ratio', type=float, default=0.99)

    parser.add_argument('--save_dir', type=str, default='ckpt/vanilla')
    parser.add_argument('--model_type', type=str, default='predictor', choices=['predictor'])
    parser.add_argument('--pred_len', type=int, default=1)
    parser.add_argument('--gpu', type=bool, default=False)
    parser.add_argument('--strong_threshold', type=float, default=0.05)
    
    args = parser.parse_args()
    main(args)