import os
import json
import torch
from datetime import datetime
from argparse import ArgumentParser
from binance import Client
from utils.preprocess import preprocess_kline
from model.kline import KlinePredictor

def predict(client, args):
    ckpt_save_dir = f'{args.save_dir}_{args.model_type}_{args.pred_len}min.pt'
    config_save_dir = f'{args.save_dir}_{args.model_type}_{args.pred_len}min.json'
    with open(config_save_dir, 'r') as f:
        config = json.load(f)

    klines = client.futures_klines(symbol='BTCUSDT', interval='1m', limit=config["data_len"]+1)[:-1]
    src, tgt = preprocess_kline(klines, config["data_len"], config["volume_normalizer"])

    if args.gpu:
        device = torch.device("cuda")
    else:
        device = torch.device("cpu")

    if args.model_type == 'predictor':
        print(f'kline last open time: {datetime.fromtimestamp(klines[-1][0]/1000)}')
        print(f'pred_datetime: {datetime.now()}')
        model = KlinePredictor(model_dim=config["model_dim"],
                               n_head=config["n_head"],
                               num_layers=config["num_layers"],
                               src_feature_dim=config["src_feature_dim"],
                               tgt_feature_dim=config["tgt_feature_dim"],
                               data_len=config["data_len"],
                               pred_len=config["pred_len"]).to(device)
        model.load_state_dict(torch.load(ckpt_save_dir))
        out = model(torch.tensor(src).to(torch.float32).to(device), torch.tensor(tgt).to(torch.float32).to(device))
        print(f'This Kline Close Price Change Rate (Predicted): {out[0][-1].item()}')
    
    return out[0][-1].item()


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
    predict(client, args)
    

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--key_path', type=str, default='./keys')
    parser.add_argument('--save_dir', type=str, default='ckpt/vanilla')
    parser.add_argument('--model_type', type=str, default='predictor', choices=['predictor'])
    parser.add_argument('--pred_len', type=int, default=1)
    parser.add_argument('--gpu', type=bool, default=False)
    args = parser.parse_args()
    main(args)