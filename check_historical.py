import pandas as pd
from argparse import ArgumentParser
from tqdm import tqdm
from datetime import datetime
from trade_signal import get_order_signal

def get_first_touch_idx(compare_list):
    if True in compare_list:
        return compare_list.index(True)
    else:
        return None

def check_performance(position, enter_price, stop_threshold, performance_window):
    high = [float(data[2]) for data in performance_window]
    low = [float(data[3]) for data in performance_window]
    
    if position == "LONG":
        above_take_profit = [price >= enter_price*(1+stop_threshold) for price in high]
        below_stop_loss = [price <= enter_price*(1-stop_threshold) for price in low]

    elif position == "SHORT":
        above_take_profit = [price <= enter_price*(1-stop_threshold) for price in low]
        below_stop_loss = [price >= enter_price*(1+stop_threshold) for price in high]
    
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
        signal = get_order_signal(data[i-args.kline_limit:i], args.kline_limit, args.check_window_len, 
                                  args.disparity_threshold, args.change_threshold)
        if signal in ["LONG", "SHORT"]:
            result = check_performance(signal, float(data[i][1]), args.stop_threshold, data[i:i+args.performance_window_len])
            signal_info = {"entry_time": datetime.fromtimestamp(int(data[i][0])/1000),
                           "enter_price": float(data[i][1]),
                           "position": signal}
            signal_info.update(result)
            signal_list.append(signal_info)
    
    df = pd.DataFrame(signal_list)
    df['time_diff'] = df['entry_time'].diff().fillna(pd.Timedelta("1day")).dt.seconds/60
    # df = df[df['time_diff'] >= pd.Timedelta("1 hour")]
    print(df)
    print(df.shape[0])
    print(df['performance'].sum())

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--data_path', type=str, default='data/BTCUSDT-1m-2024-01.csv')
    parser.add_argument('--kline_limit', type=int, default=110)
    parser.add_argument('--check_window_len', type=int, default=3)
    parser.add_argument('--performance_window_len', type=int, default=360)
    parser.add_argument('--disparity_threshold', type=float, default=20)
    parser.add_argument('--change_threshold', type=float, default=1)
    parser.add_argument('--stop_threshold', type=float, default=0.005)
    args = parser.parse_args()
    main(args)