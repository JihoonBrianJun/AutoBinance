import torch
import numpy as np
from tqdm import tqdm
from .metric_utils import compute_predictor_metrics

def test_predictor(model, loss_function, dataloader, test_bs,
                   data_len, pred_len, value_threshold, strong_threshold,
                   device, save_dir, save_ckpt=True, load_ckpt=False):
    
    if save_ckpt:
        torch.save(model.state_dict(), save_dir)
    if load_ckpt:
        model.load_state_dict(torch.load(save_dir))

    model.eval()
    test_loss = 0
    metric_list = ["correct", "rec_correct", "rec_tgt", "strong_prec_correct", "strong_prec_tgt"]
    metric_dict = dict((metric, 0) for metric in metric_list)
    
    for idx, batch in tqdm(enumerate(dataloader)):
        src = batch['src'].to(torch.float32).to(device)
        tgt = batch['tgt'].to(torch.float32).to(device)
        
        for step in range(pred_len):
            if step == 0:
                out = model(src, tgt[:,:data_len,:])
            else:
                out = model(src, torch.cat((tgt[:,:data_len,:], out[:,-step:].unsqueeze(dim=2)),dim=1))

        label = tgt[:,1:,:].squeeze(dim=2)                    
        loss = loss_function(out[:,-1],label[:,-1])
        test_loss += loss.detach().cpu().item()

        metrics = compute_predictor_metrics(out[:,-1], label[:,-1], value_threshold, strong_threshold)
        for key in metric_dict.keys():
            metric_dict[key] += metrics[key]
        
        if idx == 0:
            print(f'Out: {out[:,-1]}\n Label: {label[:,-1]}')
            
    print(f'Test Average Loss: {np.sqrt(test_loss / (idx+1))}')
    print(f'Test Correct: {metric_dict["correct"]} out of {test_bs*(idx+1)}')
    print(f'Test Recall: {metric_dict["rec_correct"]} out of {metric_dict["rec_tgt"]}')
    print(f'Test Precision (Strong): {metric_dict["strong_prec_correct"]} out of {metric_dict["strong_prec_tgt"]}')