import pandas as pd
from argparse import ArgumentParser
from tqdm import tqdm
from datetime import datetime
from trade_signal import get_momentum_signal, get_arbitrage_signal

def get_first_touch_idx(compare_list):
    if True in compare_list:
        return compare_list.index(True)
    else:
        return None


def check_momentum_performance(position, enter_price, tp_threshold, sl_threshold, performance_window):
    high = [float(data[2]) for data in performance_window]
    low = [float(data[3]) for data in performance_window]
    
    if position == "LONG":
        above_take_profit = [price >= enter_price*(1+tp_threshold) for price in high]
        below_stop_loss = [price <= enter_price*(1-sl_threshold) for price in low]

    elif position == "SHORT":
        above_take_profit = [price <= enter_price*(1-tp_threshold) for price in low]
        below_stop_loss = [price >= enter_price*(1+sl_threshold) for price in high]
    
    above_profit_idx = get_first_touch_idx(above_take_profit)
    below_loss_idx = get_first_touch_idx(below_stop_loss)
    
    if above_profit_idx is None:
        performance = False
    else:
        if below_loss_idx is None:
            performance = True
        else:
            if above_profit_idx < below_loss_idx:
                performance = True
            else:
                performance = False
    
    return {"performance": performance, "above_profit_idx": above_profit_idx, "below_loss_idx": below_loss_idx}


def check_arbitrage_performance(position, enter_price, tp_threshold, sl_threshold, performance_window):
    high = [float(data[2]) for data in performance_window]
    low = [float(data[3]) for data in performance_window]
    
    if position == "LONG":
        above_take_profit = [price >= enter_price*(1+tp_threshold) for price in high]
        below_stop_loss = [price <= enter_price*(1-sl_threshold) for price in low]

    elif position == "SHORT":
        above_take_profit = [price <= enter_price*(1-tp_threshold) for price in low]
        below_stop_loss = [price >= enter_price*(1+sl_threshold) for price in high]
    
    above_profit_idx = get_first_touch_idx(above_take_profit)
    below_loss_idx = get_first_touch_idx(below_stop_loss)
    
    if above_profit_idx is None:
        performance = False
    else:
        if below_loss_idx is None:
            performance = True
        else:
            if above_profit_idx < below_loss_idx:
                performance = True
            else:
                performance = False
    
    return {"performance": performance, "above_profit_idx": above_profit_idx, "below_loss_idx": below_loss_idx}
    

def main(args):
    with open(args.data_path, "r") as f:
        data = f.readlines()
    data = [item.split(',') for item in data][1:]
    
    signal_list = []
    for i in tqdm(range(args.kline_limit, len(data)-args.performance_window_len)):
        if args.signal_type == 'momentum':
            signal = get_momentum_signal(data[i-args.kline_limit:i], args.kline_limit, args.check_window_len,
                                         args.disparity_threshold, args.change_threshold)
            signals = [{"open": signal}]
        elif args.signal_type == 'arbitrage':
            prices = {"high": float(data[i][2]), "low": float(data[i][3])}
            signals = [{key: get_arbitrage_signal(prices[key], data[i-args.kline_limit:i], args.kline_limit, args.check_window_len,
                                                  args.change_threshold, args.arbitrage_threshold)} for key in ["high", "low"]]
        for signal_dict in signals:
            key, signal = list(signal_dict.keys())[0], list(signal_dict.values())[0]
            if signal in ["LONG", "SHORT"]:
                if args.signal_type == 'momentum':
                    enter_price = float(data[i][1])
                    result = check_momentum_performance(signal, enter_price, args.tp_threshold, args.sl_threshold, data[i:i+args.performance_window_len])                 
                elif args.signal_type == 'arbitrage':
                    if key == "high" and prices[key] >= float(data[i][1])*(1+args.arbitrage_threshold):
                        enter_price = float(data[i][1])*(1+args.arbitrage_threshold)
                    elif key == "low" and prices[key] <= float(data[i][1])*(1-args.arbitrage_threshold):
                        enter_price = float(data[i][1])*(1-args.arbitrage_threshold)
                    else:
                        continue
                    result = check_arbitrage_performance(signal, enter_price, args.tp_threshold, args.sl_threshold, data[i+1:i+args.performance_window_len])
                signal_info = {"entry_time": datetime.fromtimestamp(int(data[i][0])/1000),
                               "enter_price": enter_price,
                               "position": signal}
                if signal == "LONG":
                    signal_info["time_over_loss"] = (float(data[i+args.time_over_idx][1]) - enter_price) / enter_price
                elif signal == "SHORT":
                    signal_info["time_over_loss"] = (enter_price - float(data[i+args.time_over_idx][1])) / enter_price
                signal_info.update(result)
                signal_list.append(signal_info)

    
    df = pd.DataFrame(signal_list)
    df['time_diff'] = df['entry_time'].diff().fillna(pd.Timedelta("1day")).dt.seconds/60
    df['performance'] *= df['above_profit_idx']<=args.time_over_idx
    df['early_stop'] = df['below_loss_idx'] <= args.time_over_idx
    
    # df = df[df['time_diff'] >= pd.Timedelta("1 hour")]
    print(df.drop('time_diff', axis=1))
    print(df.shape[0])
    print(df[df['above_profit_idx']<=args.time_over_idx]['performance'].sum())
    # print(df[['above_profit_idx', 'below_loss_idx']].describe())
    print(df[~df['performance']].groupby('early_stop')[['below_loss_idx', 'time_over_loss']].describe().stack())

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--data_path', type=str, default='data/BTCUSDT-1m-2024-01.csv')
    parser.add_argument('--signal_type', type=str, default='arbitrage', choices=['momentum', 'arbitrage'])
    parser.add_argument('--kline_limit', type=int, default=110)
    parser.add_argument('--check_window_len', type=int, default=3)
    parser.add_argument('--performance_window_len', type=int, default=360)
    parser.add_argument('--disparity_threshold', type=float, default=100)
    parser.add_argument('--change_threshold', type=float, default=5)
    parser.add_argument('--arbitrage_threshold', type=float, default=0.0005)
    parser.add_argument('--tp_threshold', type=float, default=0.003)
    parser.add_argument('--sl_threshold', type=float, default=0.005)
    parser.add_argument('--time_over_idx', type=int, default=20)
    args = parser.parse_args()
    main(args)