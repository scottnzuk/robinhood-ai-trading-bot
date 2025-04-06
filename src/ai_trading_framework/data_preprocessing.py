import numpy as np
import pandas as pd
import torch
import torch.nn as nn

device = "mps" if torch.backends.mps.is_built() else "cpu"
print(f"[INFO] Using device: {device}")

class TemporalEmbedding(nn.Module):
    """
    Sinusoidal temporal embedding for timestamps or timeframes.
    """
    def __init__(self, d_model, max_len=10000):
        super().__init__()
        pe = torch.zeros(max_len, d_model, device=device)
        position = torch.arange(0, max_len).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2) * (-np.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer('pe', pe)

    def forward(self, positions):
        """
        Args:
            positions: (batch, seq_len) integer positions or timestep indices
        Returns:
            embeddings: (batch, seq_len, d_model)
        """
        return self.pe[positions]

class MultimodalPreprocessor:
    """
    Handles feature extraction, normalization, and fusion for multimodal inputs.
    """
    def __init__(self, config):
        self.config = config
        # Placeholder: Initialize scalers, NLP models, etc.
        self.scalers = {}
        self.sentiment_model = None
        self.event_encoder = None
        self.blockchain_encoder = None

    def fit_scalers(self, data_dict):
        """
        Fit normalization scalers on training data.
        """
        for key, data in data_dict.items():
            mean = np.mean(data, axis=(0,1))
            std = np.std(data, axis=(0,1)) + 1e-8
            self.scalers[key] = (mean, std)

    def transform(self, data_dict):
        """
        Normalize and encode all modalities.
        """
        out = {}
        for key, data in data_dict.items():
            mean, std = self.scalers.get(key, (0,1))
            out[key] = (data - mean) / std

        # Placeholder: NLP sentiment, event embeddings, blockchain analytics
        # These would be encoded via transformer models or other encoders
        # For now, assume precomputed vectors are passed in data_dict

        return out

    def process_batch(self, raw_batch):
        """
        Full pipeline: normalization + embeddings + fusion.
        Args:
            raw_batch: dict of raw modality data arrays
        Returns:
            dict of torch tensors ready for model input
        """
        normed = self.transform(raw_batch)
        tensors = {k: torch.tensor(v, dtype=torch.float32, device=device).clone().detach() for k,v in normed.items()}
        return tensors