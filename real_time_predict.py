import os
import torch
from datetime import datetime
from argparse import ArgumentParser
from binance import Client
from utils.preprocess import preprocess_kline
from model.kline import KlinePredictor
    
def main(args):
    with open(os.path.join(args.key_path, 'public.txt'), 'r') as f:
        for line in f.readlines():
            api_key = line
            break
    with open(os.path.join(args.key_path, 'secret.txt'), 'r') as f:
        for line in f.readlines():
            api_secret = line
            break
    ckpt_save_dir = f'{args.save_dir}_{args.model_type}_{args.pred_len}.pt'
    
    client = Client(api_key, api_secret)
    
    klines = client.futures_klines(symbol='BTCUSDT', interval='1m', limit=args.data_len+1)[:-1]
    src, tgt = preprocess_kline(klines, args.data_len, args.volume_normalizer)

    if args.gpu:
        device = torch.device("cuda")
    else:
        device = torch.device("cpu")

    if args.model_type == 'predictor':
        print(f'kline last open time: {datetime.fromtimestamp(klines[-1][0]/1000)}')
        print(f'pred_datetime: {datetime.now()}')
        model = KlinePredictor(model_dim=args.model_dim,
                               n_head=args.n_head,
                               num_layers=args.num_layers,
                               src_feature_dim=args.src_feature_dim,
                               tgt_feature_dim=args.tgt_feature_dim,
                               data_len=args.data_len,
                               pred_len=args.pred_len).to(device)
        model.load_state_dict(torch.load(ckpt_save_dir))
        out = model(torch.tensor(src).to(torch.float32).to(device), torch.tensor(tgt).to(torch.float32).to(device))
        print(f'This Kline Close Price Change Rate (Predicted): {out[0][-1].item()}')
    

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--key_path', type=str, default='./keys')
    parser.add_argument('--save_dir', type=str, default='ckpt/vanilla')
    parser.add_argument('--model_type', type=str, default='predictor', choices=['predictor'])
    parser.add_argument('--kline_limit', type=int, default=110)
    parser.add_argument('--data_len', type=int, default=100)
    parser.add_argument('--pred_len', type=int, default=1)
    parser.add_argument('--volume_normalizer', type=float, default=5)
    parser.add_argument('--model_dim', type=int, default=512)
    parser.add_argument('--n_head', type=int, default=8)
    parser.add_argument('--num_layers', type=int, default=6)
    parser.add_argument('--src_feature_dim', type=int, default=5)
    parser.add_argument('--tgt_feature_dim', type=int, default=1)
    parser.add_argument('--gpu', type=bool, default=False)
    parser.add_argument('--value_threshold', type=float, default=0.1)
    parser.add_argument('--strong_threshold', type=float, default=0.1)
    args = parser.parse_args()
    main(args)