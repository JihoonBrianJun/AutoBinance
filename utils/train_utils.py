import torch
import numpy as np
from tqdm import tqdm
from .test_utils import test_predictor

def train_predictor(model, optimizer, scheduler, loss_function,
                    train_loader, test_loader, test_bs,
                    data_len, pred_len, value_threshold, strong_threshold,
                    epoch, device, save_dir):
    
    best_test_loss = np.inf
    for epoch in tqdm(range(epoch)):
        if epoch % 10 == 0:
            test_loss = test_predictor(model, loss_function, test_loader, test_bs,
                                       data_len, pred_len, value_threshold, strong_threshold,
                                       device, save_dir, best_test_loss)
            if test_loss < best_test_loss:
                best_test_loss = test_loss

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
        
        if epoch_avg_loss < best_test_loss:
            print(f"Train early stop at epoch {epoch} (epoch_loss={epoch_avg_loss}, best_val_loss={best_test_loss})")
            break
    
    test_predictor(model, loss_function, test_loader, test_bs,
                   data_len, pred_len, value_threshold, strong_threshold,
                   device, save_dir)