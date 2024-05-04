import torch
import numpy as np
from tqdm import tqdm
from .test_utils import test_predictor

def train_predictor(model, optimizer, scheduler, loss_function,
                    train_loader, test_loader, test_bs,
                    data_len, pred_len, value_threshold, strong_threshold,
                    epoch, stop_loss_ratio, stop_correct_threshold, 
                    device, save_dir, train_config):
    
    best_test_loss = np.inf
    best_test_score = 0
    for epoch in tqdm(range(epoch)):
        if epoch % 10 == 0 and epoch != 0:
            test_loss, correct_rate, test_score = test_predictor(model, loss_function, test_loader, test_bs,
                                                                 data_len, pred_len, value_threshold, strong_threshold,
                                                                 device, save_dir, train_config, best_test_loss, best_test_score)
            if test_loss < best_test_loss:
                best_test_loss = test_loss
            if test_score > best_test_score:
                best_test_score = test_score

        model.train()
        epoch_loss = 0
        for idx, batch in tqdm(enumerate(train_loader)):
            src = batch['src'].to(torch.float32).to(device)
            tgt = batch['tgt'].to(torch.float32).to(device)
            
            for step in range(pred_len):
                out = model(src, tgt[:,:data_len+step,:])
                label = tgt[:,1:data_len+step+1,:].squeeze(dim=2)
                loss = loss_function(out,label)
                loss.backward()

                optimizer.step()
                optimizer.zero_grad()
            
            epoch_loss += loss.detach().cpu().item()     
        
        epoch_avg_loss = np.sqrt(epoch_loss/(idx+1))
        print(f'Epoch {epoch} Average Loss: {epoch_avg_loss}')
        scheduler.step()
        
        if epoch >= 10:
            if epoch_avg_loss < best_test_loss * stop_loss_ratio or correct_rate >= stop_correct_threshold:
                print(f"Train early stop at epoch {epoch} (epoch_loss={epoch_avg_loss}, best_val_loss={best_test_loss})")
                break
    
    test_predictor(model, loss_function, test_loader, test_bs,
                   data_len, pred_len, value_threshold, strong_threshold,
                   device, save_dir, train_config, save_ckpt=False, load_ckpt=True)