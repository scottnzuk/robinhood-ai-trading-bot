import torch
import torch.nn as nn

class HybridLSTMTransformer(nn.Module):
    def __init__(self, input_dim, lstm_hidden=128, trans_heads=4, trans_layers=2, trans_dim=128, output_dim=3):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, lstm_hidden, batch_first=True, num_layers=2, bidirectional=True)
        self.lstm_out_dim = lstm_hidden * 2

        encoder_layer = nn.TransformerEncoderLayer(d_model=self.lstm_out_dim, nhead=trans_heads, dim_feedforward=trans_dim, batch_first=True)
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=trans_layers)

        self.head = nn.Sequential(
            nn.Linear(self.lstm_out_dim, 64),
            nn.ReLU(),
            nn.Linear(64, output_dim)  # e.g., 3 outputs: up/down/neutral or regression targets
        )

    def forward(self, x):
        # x: (batch, seq_len, features)
        lstm_out, _ = self.lstm(x)  # (batch, seq_len, hidden*2)
        trans_out = self.transformer(lstm_out)  # (batch, seq_len, hidden*2)
        pooled = trans_out.mean(dim=1)  # global average pooling over time
        out = self.head(pooled)
        return out