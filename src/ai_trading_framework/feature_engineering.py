import numpy as np
import pandas as pd
import torch
import torch.nn as nn

device = "mps" if torch.backends.mps.is_built() else "cpu"
print(f"[INFO] Using device: {device}")

class FeatureEngineer:
    def __init__(self, config=None):
        self.config = config or {}
        self.scalers = {}

    def fit_scalers(self, data_dict):
        for key, df in data_dict.items():
            mean = df.mean()
            std = df.std() + 1e-8
            self.scalers[key] = (mean, std)

    def transform(self, data_dict):
        out = {}
        for key, df in data_dict.items():
            mean, std = self.scalers.get(key, (0,1))
            out[key] = (df - mean) / std
        return out

    def compute_technical_indicators(self, df):
        df['ema_20'] = df['close'].ewm(span=20).mean()
        df['rsi_14'] = self.rsi(df['close'], 14)
        df['macd'] = df['close'].ewm(span=12).mean() - df['close'].ewm(span=26).mean()
        df['bollinger_upper'] = df['close'].rolling(20).mean() + 2*df['close'].rolling(20).std()
        df['bollinger_lower'] = df['close'].rolling(20).mean() - 2*df['close'].rolling(20).std()
        df['vwap'] = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()
        return df

    def rsi(self, series, period=14):
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / (loss + 1e-8)
        return 100 - (100 / (1 + rs))

    def engineer_order_book_features(self, order_book_df):
        order_book_df['spread'] = order_book_df['ask'] - order_book_df['bid']
        order_book_df['imbalance'] = (order_book_df['bid_size'] - order_book_df['ask_size']) / (order_book_df['bid_size'] + order_book_df['ask_size'] + 1e-8)
        return order_book_df

    def embed_sentiment_event_blockchain(self, sentiment_vecs, event_vecs, blockchain_vecs):
        # Placeholder: assume already embedded vectors
        return sentiment_vecs, event_vecs, blockchain_vecs

    def adaptive_feature_selection(self, features_df):
        # Placeholder: simple variance threshold
        variances = features_df.var()
        selected = variances[variances > 1e-4].index
        return features_df[selected]

    def process_all(self, data_dict, order_book_df, sentiment_vecs, event_vecs, blockchain_vecs):
        normed = self.transform(data_dict)
        tech_feats = {}
        for key, df in normed.items():
            df = self.compute_technical_indicators(df)
            tech_feats[key] = df

        order_feats = self.engineer_order_book_features(order_book_df)
        sent_vecs, event_vecs, chain_vecs = self.embed_sentiment_event_blockchain(sentiment_vecs, event_vecs, blockchain_vecs)

        # Concatenate all features
        combined = pd.concat(list(tech_feats.values()) + [order_feats], axis=1)
        combined = self.adaptive_feature_selection(combined)

        # Convert to torch tensor
        tensor_feats = torch.tensor(combined.fillna(0).values, dtype=torch.float32, device=device).clone().detach()

        # Also return embeddings separately
        return {
            "features": tensor_feats,
            "sentiment": torch.tensor(sent_vecs, dtype=torch.float32, device=device).clone().detach(),
            "events": torch.tensor(event_vecs, dtype=torch.float32, device=device).clone().detach(),
            "blockchain": torch.tensor(chain_vecs, dtype=torch.float32, device=device).clone().detach()
        }