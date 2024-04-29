import torch

def compute_predictor_metrics(pred, target, value_threshold, strong_threshold):
    metrics = dict()
    metrics["correct"] = ((pred*target)>0).sum().item()

    metrics["rec_tgt"] = (target>=value_threshold).to(torch.long).sum().item()
    metrics["rec_correct"] = ((target>=value_threshold).to(torch.long) * (pred>0).to(torch.long)).sum().item()

    metrics["strong_prec_tgt"] = (pred>=strong_threshold).to(torch.long).sum().item()
    metrics["strong_prec_correct"] = ((pred>=strong_threshold).to(torch.long) * (target>0).to(torch.long)).sum().item()

    return metrics