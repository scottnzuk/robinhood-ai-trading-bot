import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

class HybridAgentTrainer:
    """
    Trainer for the hybrid multimodal agent with continual learning and probabilistic multi-horizon losses.
    """

    def __init__(self, model, optimizer, horizons=(10, 60, 240), device='cpu'):
        self.model = model
        self.optimizer = optimizer
        self.horizons = horizons
        self.device = device
        self.replay_buffer = []

    def gaussian_nll(self, mean, log_var, target):
        return 0.5 * log_var + 0.5 * ((target - mean) ** 2) / torch.exp(log_var)

    def asymmetric_huber(self, pred, target, delta=1.0, asymmetry=2.0):
        diff = pred - target
        loss = torch.where(
            diff > delta,
            asymmetry * (diff - delta) + 0.5 * delta,
            torch.where(
                diff < -delta,
                (diff + delta) + 0.5 * delta,
                0.5 * diff ** 2
            )
        )
        return loss

    def compute_loss(self, outputs, targets, aux_targets=None):
        total_loss = 0.0
        for horizon in self.horizons:
            out = outputs[horizon]
            mean = out['mean']
            log_var = out['log_var']
            aux_logits = out['aux_logits']

            target = targets[horizon].to(self.device)

            nll = self.gaussian_nll(mean, log_var, target).mean()

            # Optional: asymmetric huber penalty
            huber = self.asymmetric_huber(mean, target).mean()

            # Auxiliary classification loss
            aux_loss = 0.0
            if aux_targets is not None:
                aux_target = aux_targets[horizon].to(self.device)
                aux_loss = F.binary_cross_entropy_with_logits(aux_logits, aux_target.float())

            total_loss += nll + 0.1 * huber + 0.1 * aux_loss

        return total_loss

    def update(self, batch_inputs, batch_targets, aux_targets=None):
        self.model.train()
        outputs = self.model(batch_inputs)
        loss = self.compute_loss(outputs, batch_targets, aux_targets)

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        return loss.item()

    def add_to_replay(self, batch_inputs, batch_targets, aux_targets=None):
        self.replay_buffer.append((batch_inputs, batch_targets, aux_targets))
        if len(self.replay_buffer) > 10000:
            self.replay_buffer.pop(0)

    def continual_update(self, batch_size=32):
        if len(self.replay_buffer) < batch_size:
            return None
        idx = np.random.choice(len(self.replay_buffer), batch_size, replace=False)
        batch = [self.replay_buffer[i] for i in idx]
        inputs = {}
        targets = {}
        aux_targets = {}

        # Aggregate batches
        for key in batch[0][0]:
            inputs[key] = torch.cat([b[0][key] for b in batch], dim=0)
        for horizon in self.horizons:
            targets[horizon] = torch.cat([b[1][horizon] for b in batch], dim=0)
            if batch[0][2] is not None:
                aux_targets[horizon] = torch.cat([b[2][horizon] for b in batch], dim=0)
            else:
                aux_targets = None

        return self.update(inputs, targets, aux_targets)