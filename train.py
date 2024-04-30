import os
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torch.optim.lr_scheduler import StepLR
from argparse import ArgumentParser
from utils.preprocess import preprocess_csv
from utils.train_utils import train_predictor
from model.kline import KlinePredictor


def main(args):
    save_dir = f'{args.save_dir}_{args.train_type}_{args.pred_len}min'
    if not os.path.exists(save_dir.split('/')[0]):
        os.makedirs(save_dir.split('/')[0])
    train_config = {"train_type": args.train_type,
                    "data_len": args.data_len,
                    "pred_len": args.pred_len,
                    "volume_normalizer": args.volume_normalizer,
                    "model_dim": args.model_dim,
                    "n_head": args.n_head,
                    "num_layers": args.num_layers,
                    "src_feature_dim": args.src_feature_dim,
                    "tgt_feature_dim": args.tgt_feature_dim,
                    "initial_lr": args.lr,
                    "gamma": args.gamma}
    
    data = np.array(preprocess_csv(args.data_path, args.data_len, args.data_hop, args.pred_len, args.volume_normalizer))
    
    train_idx = np.random.choice(np.arange(len(data)), size=int(len(data)*args.train_ratio), replace=False)
    test_idx = np.array(list(set(np.arange(len(data)).tolist()).difference(set(train_idx.tolist()))))
    
    train_loader = DataLoader(data[train_idx], batch_size=args.bs, shuffle=True)
    test_bs = min(len(test_idx),args.bs)
    test_loader = DataLoader(data[test_idx], batch_size=test_bs, shuffle=True)
    
    if args.gpu:
        device = torch.device("cuda")
    else:
        device = torch.device("cpu")
    
    if args.train_type == 'predictor':
        model = KlinePredictor(model_dim=args.model_dim,
                               n_head=args.n_head,
                               num_layers=args.num_layers,
                               src_feature_dim=args.src_feature_dim,
                               tgt_feature_dim=args.tgt_feature_dim,
                               data_len=args.data_len,
                               pred_len=args.pred_len).to(device)

    num_param = 0
    for _, param in model.named_parameters():
        num_param += param.numel()
    print(f'model param size: {num_param}')
    
    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.lr*10)
    scheduler = StepLR(optimizer, step_size=1, gamma=args.gamma)
    
    if args.train_type == 'predictor':
        loss_function = nn.MSELoss()
        train_predictor(model=model,
                        optimizer=optimizer,
                        scheduler=scheduler,
                        loss_function=loss_function,
                        train_loader=train_loader,
                        test_loader=test_loader,
                        test_bs=test_bs,
                        data_len=args.data_len,
                        pred_len=args.pred_len,
                        value_threshold=args.value_threshold, 
                        strong_threshold=args.strong_threshold,
                        epoch=args.epoch,
                        stop_loss_ratio=args.stop_loss_ratio,
                        stop_correct_threshold=args.stop_correct_threshold,
                        device=device,
                        save_dir=save_dir,
                        train_config=train_config)

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--data_path', type=str, default='data/2024_100days.csv')
    parser.add_argument('--save_dir', type=str, default='ckpt/vanilla')
    parser.add_argument('--train_type', type=str, default='predictor', choices=['predictor'])
    parser.add_argument('--data_len', type=int, default=100)
    parser.add_argument('--pred_len', type=int, default=1)
    parser.add_argument('--data_hop', type=int, default=10)
    parser.add_argument('--volume_normalizer', type=float, default=5)
    parser.add_argument('--train_ratio', type=float, default=0.99)
    parser.add_argument('--model_dim', type=int, default=512)
    parser.add_argument('--n_head', type=int, default=8)
    parser.add_argument('--num_layers', type=int, default=6)
    parser.add_argument('--src_feature_dim', type=int, default=5)
    parser.add_argument('--tgt_feature_dim', type=int, default=1)
    parser.add_argument('--epoch', type=int, default=1000)
    parser.add_argument('--bs', type=int, default=200)
    parser.add_argument('--gpu', type=bool, default=True)
    parser.add_argument('--lr', type=float, default=1e-5)
    parser.add_argument('--gamma', type=float, default=0.999)
    parser.add_argument('--value_threshold', type=float, default=0.1)
    parser.add_argument('--strong_threshold', type=float, default=0.05)
    parser.add_argument('--stop_loss_ratio', type=float, default=0.9)
    parser.add_argument('--stop_correct_threshold', type=float, default=0.6)
    args = parser.parse_args()
    main(args)