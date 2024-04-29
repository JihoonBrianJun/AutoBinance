import numpy as np
import pandas as pd
from tqdm import tqdm

def preprocess(data_path, data_len, data_hop, pred_len, volume_normalizer):
    df = pd.read_csv(data_path).sort_values(by='open_time').reset_index(drop=True)
    for volume_key in ['volume', 'taker_buy_volume']:
        df[volume_key] = df[volume_key].apply(lambda x: np.log(x)) - volume_normalizer
    df = df[['open', 'high', 'low', 'close', 'volume', 'taker_buy_volume']]

    window_size = data_len + pred_len
    data = []
    for idx in tqdm(range((df.shape[0]-window_size)//data_hop)):
        df_window = df.iloc[idx*data_hop:idx*data_hop+window_size]
        window_base_price = df_window['close'].iloc[-2]
        for price_key in ['open', 'high', 'low', 'close']:
            df_window[price_key] = (df_window[price_key] - window_base_price) / window_base_price * 100
        src = df_window.drop(['close'], axis=1).to_numpy()[:data_len]
        tgt = df_window[['close']].to_numpy()
        data.append({'src': src, 'tgt': tgt})
    
    return data