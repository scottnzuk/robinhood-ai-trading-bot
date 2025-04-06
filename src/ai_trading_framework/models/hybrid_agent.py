import torch
import torch.nn as nn
import torch.nn.functional as F

class HybridMultimodalAgent(nn.Module):
    """
    Advanced hybrid LSTM + Transformer neural agent for multimodal, multi-horizon forecasting.
    """

    def __init__(
        self,
        input_dims,
        lstm_hidden_dim=256,
        lstm_layers=2,
        transformer_dim=256,
        transformer_heads=8,
        transformer_layers=4,
        forecast_horizons=(10, 60, 240),  # e.g., 10min, 1h, 4h
        dropout=0.1,
    ):
        """
        Args:
            input_dims (dict): Dict of modality name to input feature dimension.
            lstm_hidden_dim (int): Hidden size for LSTM layers.
            lstm_layers (int): Number of LSTM layers.
            transformer_dim (int): Transformer embedding dimension.
            transformer_heads (int): Number of Transformer heads.
            transformer_layers (int): Number of Transformer encoder layers.
            forecast_horizons (tuple): Time horizons for multi-horizon forecasting.
            dropout (float): Dropout rate.
        """
        super().__init__()
        self.modalities = list(input_dims.keys())
        self.forecast_horizons = forecast_horizons

        # Per-modality encoders (simple linear projections for now)
        self.encoders = nn.ModuleDict({
            mod: nn.Linear(input_dims[mod], transformer_dim) for mod in self.modalities
        })

        # LSTM backbone for sequential modeling
        self.lstm = nn.LSTM(
            input_size=transformer_dim * len(self.modalities),
            hidden_size=lstm_hidden_dim,
            num_layers=lstm_layers,
            batch_first=True,
            dropout=dropout,
            bidirectional=False,
        )

        # Transformer encoder for capturing long-range dependencies
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=lstm_hidden_dim,
            nhead=transformer_heads,
            dim_feedforward=transformer_dim * 4,
            dropout=dropout,
            activation='gelu',
            batch_first=True,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=transformer_layers)

        # Multi-horizon probabilistic forecasting heads
        self.heads = nn.ModuleDict()
        for horizon in forecast_horizons:
            self.heads[str(horizon)] = nn.Linear(lstm_hidden_dim, 3)  # mean, log_var, auxiliary classification

    def forward(self, inputs):
        """
        Args:
            inputs (dict): Dict of modality name to tensor of shape (batch, seq_len, feat_dim).
        Returns:
            dict: Multi-horizon forecasts with mean, log_var, and auxiliary logits.
        """
        # Encode each modality separately
        encoded = []
        for mod in self.modalities:
            x = inputs[mod]  # (batch, seq_len, feat_dim)
            x_proj = self.encoders[mod](x)  # (batch, seq_len, transformer_dim)
            encoded.append(x_proj)

        # Concatenate along feature dimension
        x_cat = torch.cat(encoded, dim=-1)  # (batch, seq_len, transformer_dim * num_modalities)

        # LSTM backbone
        lstm_out, _ = self.lstm(x_cat)  # (batch, seq_len, lstm_hidden_dim)

        # Transformer encoder
        trans_out = self.transformer(lstm_out)  # (batch, seq_len, lstm_hidden_dim)

        # Use last time step for forecasting
        last_hidden = trans_out[:, -1, :]  # (batch, lstm_hidden_dim)

        # Multi-horizon outputs
        outputs = {}
        for horizon in self.forecast_horizons:
            out = self.heads[str(horizon)](last_hidden)  # (batch, 3)
            mean = out[:, 0]
            log_var = out[:, 1]
            aux_logits = out[:, 2]
            outputs[horizon] = {
                'mean': mean,
                'log_var': log_var,
                'aux_logits': aux_logits,
            }

        return outputs