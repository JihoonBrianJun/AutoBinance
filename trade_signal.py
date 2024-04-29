import math

def get_momentum_signal(klines, kline_limit, check_window_len, disparity_threshold, change_threshold):
    position = False
    
    up_down = [float(kline[4])>float(kline[1]) for kline in klines[-check_window_len:]]
    close = [float(kline[4]) for kline in klines]

    ma_7 = [sum(close[i-6:i+1])/7 for i in range(kline_limit - check_window_len, kline_limit)]
    ma_25 = [sum(close[i-24:i+1])/25 for i in range(kline_limit - check_window_len, kline_limit)]
    ma_99 = [sum(close[i-98:i+1])/99 for i in range(kline_limit - check_window_len, kline_limit)]
    
    if sum(up_down) == check_window_len:
        # ma25_pos = [ma_25[i]-ma_7[i] > disparity_threshold for i in range(check_window_len)]
        # ma99_pos = [ma_7[i]<ma_99[i] for i in range(check_window_len)]
        # if sum(ma25_pos) == check_window_len and sum(ma99_pos) == check_window_len:
        if ma_25[0] - ma_7[0] > disparity_threshold and ma_99[0] > ma_7[0]:
            ma25_change = [ma_25[i+1]-ma_25[i] >= -change_threshold for i in range(check_window_len-1)]
            ma99_change = [ma_99[i+1]-ma_99[i] >= -change_threshold for i in range(check_window_len-1)]
            if sum(ma25_change) == check_window_len-1 and sum(ma99_change) == check_window_len-1:
                position = "LONG"
                        
    elif sum(up_down) == 0:
        # ma25_pos = [ma_7[i] - ma_25[i] > disparity_threshold for i in range(check_window_len)]
        # ma99_pos = [ma_7[i]>ma_99[i] for i in range(check_window_len)]
        # if sum(ma25_pos) == check_window_len and sum(ma99_pos) == check_window_len:
        if ma_7[0] - ma_25[0] > disparity_threshold and ma_7[0] > ma_99[0]:
            ma25_change = [ma_25[i+1]-ma_25[i] <= change_threshold for i in range(check_window_len-1)]
            ma99_change = [ma_99[i+1]-ma_99[i] <= change_threshold for i in range(check_window_len-1)]
            if sum(ma25_change) == check_window_len-1 and sum(ma99_change) == check_window_len-1:
                position = "SHORT"

    return position


def get_arbitrage_signal(price, klines, kline_limit, check_window_len, change_threshold, arbitrage_threshold):
    position = False
    
    close = [float(kline[4]) for kline in klines]
    ma_7 = [sum(close[i-6:i+1])/7 for i in range(kline_limit - check_window_len, kline_limit)]
    ma_25 = [sum(close[i-24:i+1])/25 for i in range(kline_limit - check_window_len, kline_limit)]
    ma_99 = [sum(close[i-98:i+1])/99 for i in range(kline_limit - check_window_len, kline_limit)]
    
    ma_7_flat_check = sum([math.fabs(ma_7[i+1] - ma_7[i])<=change_threshold for i in range(check_window_len-1)])
    
    if ma_7_flat_check == check_window_len-1:
        ma25_pos = [ma_7[i] - ma_25[i] > 0 for i in range(check_window_len)]
        ma99_pos = [ma_7[i] - ma_99[i] > 0 for i in range(check_window_len)]
        # if sum(ma25_pos) == check_window_len and sum(ma99_pos) == check_window_len:
        if sum(ma25_pos) == check_window_len:
            # ma_25_flat_check = sum([ma_25[i+1] - ma_25[i] <= change_threshold for i in range(check_window_len-1)])
            # ma_99_flat_check = sum([ma_99[i+1] - ma_99[i] <= change_threshold for i in range(check_window_len-1)])
            # if ma_25_flat_check == check_window_len-1 and ma_99_flat_check == check_window_len-1:
            if True:
                if (price-ma_7[-1])/ma_7[-1] >= arbitrage_threshold:
                    position = "SHORT"
        # elif sum(ma25_pos) == 0 and sum(ma99_pos) == 0:
        elif sum(ma25_pos) == 0:
            # ma_25_flat_check = sum([ma_25[i+1] - ma_25[i] >= -change_threshold for i in range(check_window_len-1)])
            # ma_99_flat_check = sum([ma_99[i+1] - ma_99[i] >= -change_threshold for i in range(check_window_len-1)])
            # if ma_25_flat_check == 0 and ma_99_flat_check == 0:
            if True:
                if (price-ma_7[-1])/ma_7[-1] <= -arbitrage_threshold:
                    position = "LONG"
    
    return position