import numpy as np
import pandas as pd
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class RawDataPoint:
    timestamp: pd.Timestamp
    symbol: str
    price: float
    volume: float
    additional_data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FeatureVector:
    timestamp: pd.Timestamp
    symbol: str
    features: Dict[str, float]

@dataclass
class FeatureMetadata:
    feature_name: str
    description: str
    source: str
    params: Dict[str, Any] = field(default_factory=dict)

class BaseFeatureModule(ABC):
    """
    Abstract base class for all feature modules.
    """
    @abstractmethod
    def compute(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Compute features from input data.
        Returns a DataFrame with new feature columns.
        """
        pass

class TechnicalIndicatorsModule(BaseFeatureModule):
    """
    Computes multi-timeframe technical indicators like MA, RSI, MACD, ATR.
    """
    def __init__(self, timeframes: List[str] = ["5min", "15min", "1H", "1D"], ma_periods: List[int] = [20, 50], rsi_period: int = 14, atr_period: int = 14):
        self.timeframes = timeframes
        self.ma_periods = ma_periods
        self.rsi_period = rsi_period
        self.atr_period = atr_period

    def compute(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Compute multi-timeframe technical indicators and add them as columns.
        Assumes 'timestamp', 'symbol', 'price', 'high', 'low', 'close', 'volume' columns exist.
        """
        data = data.copy()
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        data.set_index('timestamp', inplace=True)

        # For each timeframe, resample and compute indicators
        for tf in self.timeframes:
            df_resampled = data.groupby('symbol').resample(tf).agg({
                'price': 'last',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna().reset_index().set_index('timestamp')

            for period in self.ma_periods:
                sma = df_resampled.groupby('symbol')['close'].transform(lambda x: x.rolling(window=period).mean())
                ema = df_resampled.groupby('symbol')['close'].transform(lambda x: x.ewm(span=period, adjust=False).mean())
                df_resampled[f'sma_{tf}_{period}'] = sma
                df_resampled[f'ema_{tf}_{period}'] = ema

            # RSI
            def compute_rsi(series, period):
                delta = series.diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                rs = gain / (loss + 1e-9)
                return 100 - (100 / (1 + rs))

            df_resampled[f'rsi_{tf}_{self.rsi_period}'] = df_resampled.groupby('symbol')['close'].transform(lambda x: compute_rsi(x, self.rsi_period))

            # MACD
            ema_fast = df_resampled.groupby('symbol')['close'].transform(lambda x: x.ewm(span=12, adjust=False).mean())
            ema_slow = df_resampled.groupby('symbol')['close'].transform(lambda x: x.ewm(span=26, adjust=False).mean())
            macd = ema_fast - ema_slow
            signal = macd.ewm(span=9, adjust=False).mean()
            df_resampled[f'macd_{tf}'] = macd
            df_resampled[f'macd_signal_{tf}'] = signal

            # ATR
            def compute_atr(df, period):
                high_low = df['high'] - df['low']
                high_close = (df['high'] - df['close'].shift()).abs()
                low_close = (df['low'] - df['close'].shift()).abs()
                tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
                atr = tr.rolling(window=period).mean()
                return atr

            df_resampled[f'atr_{tf}_{self.atr_period}'] = df_resampled.groupby('symbol').apply(lambda g: compute_atr(g, self.atr_period)).reset_index(level=0, drop=True)

            # Merge back to original data
            data = data.merge(df_resampled.drop(columns=['price', 'high', 'low', 'close', 'volume']),
                              left_on=['timestamp', 'symbol'],
                              right_on=['timestamp', 'symbol'],
                              how='left')

        data.reset_index(inplace=True)
        return data

class CorrelationFeaturesModule(BaseFeatureModule):
    """
    Computes cross-asset correlation features.
    """
    def __init__(self, correlation_symbols: List[str] = ["SPY", "QQQ", "BTC"], window: int = 20):
        self.correlation_symbols = correlation_symbols
        self.window = window

    def compute(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Compute rolling correlations with specified assets.
        Assumes 'symbol', 'timestamp', 'close' columns.
        """
        data = data.copy()
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        data.set_index('timestamp', inplace=True)

        # Pivot to symbol x time matrix
        close_pivot = data.pivot_table(index='timestamp', columns='symbol', values='close')

        for sym in self.correlation_symbols:
            if sym not in close_pivot.columns:
                continue  # skip missing symbols

            for target_sym in close_pivot.columns:
                if target_sym == sym:
                    continue

                corr = close_pivot[sym].rolling(window=self.window).corr(close_pivot[target_sym])
                feature_name = f"corr_{target_sym}_{sym}_{self.window}"
                # Add back to data
                corr_df = corr.to_frame(name=feature_name).reset_index()
                corr_df['symbol'] = target_sym

                data = data.reset_index().merge(corr_df, on=['timestamp', 'symbol'], how='left').set_index('timestamp')

        data.reset_index(inplace=True)
        return data

class SentimentFeaturesModule(BaseFeatureModule):
    """
    Computes sentiment and event-driven features.
    """
    def __init__(self, sentiment_data: Optional[pd.DataFrame] = None, event_data: Optional[pd.DataFrame] = None):
        """
        sentiment_data: DataFrame with ['timestamp', 'symbol', 'sentiment_score']
        event_data: DataFrame with ['timestamp', 'symbol', 'event_type']
        """
        self.sentiment_data = sentiment_data
        self.event_data = event_data

    def compute(self, data: pd.DataFrame) -> pd.DataFrame:
        data = data.copy()
        data['timestamp'] = pd.to_datetime(data['timestamp'])

        # Merge sentiment scores
        if self.sentiment_data is not None:
            sentiment = self.sentiment_data.copy()
            sentiment['timestamp'] = pd.to_datetime(sentiment['timestamp'])
            data = data.merge(sentiment, on=['timestamp', 'symbol'], how='left')
            data['sentiment_score'] = data['sentiment_score'].ffill().fillna(0)

        # Merge event flags
        if self.event_data is not None:
            event = self.event_data.copy()
            event['timestamp'] = pd.to_datetime(event['timestamp'])
            # One-hot encode event types
            event_dummies = pd.get_dummies(event['event_type'], prefix='event')
            event = pd.concat([event[['timestamp', 'symbol']], event_dummies], axis=1)
            data = data.merge(event, on=['timestamp', 'symbol'], how='left')
            # Fill missing event flags with 0
            event_cols = [col for col in data.columns if col.startswith('event_')]
            data[event_cols] = data[event_cols].fillna(0)

        return data

class VolatilityFeaturesModule(BaseFeatureModule):
    """
    Computes volatility and liquidity metrics.
    """
    def __init__(self, window: int = 20):
        self.window = window

    def compute(self, data: pd.DataFrame) -> pd.DataFrame:
        data = data.copy()
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        data.sort_values(['symbol', 'timestamp'], inplace=True)

        # Compute log returns
        data['log_return'] = data.groupby('symbol')['close'].transform(lambda x: np.log(x).diff())

        # Rolling volatility (std dev of returns)
        data[f'volatility_{self.window}'] = data.groupby('symbol')['log_return'].transform(lambda x: x.rolling(window=self.window).std())

        # Volume ratio (current volume / rolling mean volume)
        data[f'volume_ratio_{self.window}'] = data.groupby('symbol')['volume'].transform(lambda x: x / (x.rolling(window=self.window).mean() + 1e-9))

        # VWAP deviation (close - VWAP) / VWAP
        data['vwap'] = data.groupby('symbol').apply(
            lambda g: (g['close'] * g['volume']).cumsum() / (g['volume'].cumsum() + 1e-9)
        ).reset_index(level=0, drop=True)
        data[f'vwap_deviation_{self.window}'] = (data['close'] - data['vwap']) / (data['vwap'] + 1e-9)

        # Drop intermediate columns
        data.drop(columns=['log_return', 'vwap'], inplace=True)

        return data

from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

class FeatureSelector:
    """
    Handles feature normalization, dimensionality reduction, importance ranking, and pruning.
    """
    def __init__(self, pca_variance: float = 0.95):
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=pca_variance)

    def normalize(self, features: pd.DataFrame) -> pd.DataFrame:
        numeric_cols = features.select_dtypes(include=[np.number]).columns
        features[numeric_cols] = self.scaler.fit_transform(features[numeric_cols])
        return features

    def reduce_dimensionality(self, features: pd.DataFrame) -> pd.DataFrame:
        numeric_cols = features.select_dtypes(include=[np.number]).columns
        reduced = self.pca.fit_transform(features[numeric_cols])
        reduced_df = pd.DataFrame(reduced, index=features.index, columns=[f'pca_{i}' for i in range(reduced.shape[1])])
        # Concatenate non-numeric columns + reduced features
        non_numeric = features.drop(columns=numeric_cols)
        return pd.concat([non_numeric.reset_index(drop=True), reduced_df.reset_index(drop=True)], axis=1)

    def rank_features(self, features: pd.DataFrame, labels: pd.Series) -> Dict[str, float]:
        # Placeholder: simple correlation-based importance
        scores = {}
        numeric_cols = features.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            try:
                scores[col] = abs(np.corrcoef(features[col], labels)[0,1])
            except Exception:
                scores[col] = 0.0
        return scores

    def prune_features(self, features: pd.DataFrame, importance_scores: Dict[str, float], threshold: float = 0.01) -> pd.DataFrame:
        keep_cols = [col for col, score in importance_scores.items() if score >= threshold]
        non_numeric = features.select_dtypes(exclude=[np.number]).columns.tolist()
        return features[non_numeric + keep_cols]

from statsmodels.tsa.stattools import adfuller

class FeatureValidator:
    """
    Performs validation: stationarity, correlation, leakage detection, outlier handling, drift monitoring.
    """
    def validate_stationarity(self, features: pd.DataFrame) -> Dict[str, bool]:
        results = {}
        numeric_cols = features.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            try:
                pvalue = adfuller(features[col].dropna())[1]
                results[col] = pvalue < 0.05  # True if stationary
            except Exception:
                results[col] = False
        return results

    def detect_leakage(self, features: pd.DataFrame, labels: pd.Series) -> bool:
        # Simple leakage detection: high correlation with future labels
        leakage_found = False
        shifted_labels = labels.shift(-1)
        numeric_cols = features.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            try:
                corr = abs(np.corrcoef(features[col].iloc[:-1], shifted_labels.iloc[:-1])[0,1])
                if corr > 0.8:
                    leakage_found = True
            except Exception:
                continue
        return leakage_found

    def handle_outliers(self, features: pd.DataFrame, lower_quantile=0.01, upper_quantile=0.99) -> pd.DataFrame:
        numeric_cols = features.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            q_low = features[col].quantile(lower_quantile)
            q_high = features[col].quantile(upper_quantile)
            features[col] = features[col].clip(q_low, q_high)
        return features

    def monitor_drift(self, features: pd.DataFrame) -> Dict[str, Any]:
        # Placeholder: implement PSI or KS test in future
        return {}

class FeaturePipeline:
    """
    Orchestrates feature computation, selection, and validation.
    """
    def __init__(self, modules: Optional[List[BaseFeatureModule]] = None):
        self.modules = modules or [
            TechnicalIndicatorsModule(),
            CorrelationFeaturesModule(),
            SentimentFeaturesModule(),
            VolatilityFeaturesModule()
        ]
        self.selector = FeatureSelector()
        self.validator = FeatureValidator()

    def run(self, data: pd.DataFrame, labels: Optional[pd.Series] = None) -> pd.DataFrame:
        """
        Execute the full feature engineering pipeline.
        """
        for module in self.modules:
            data = module.compute(data)

        data = self.selector.normalize(data)
        data = self.selector.reduce_dimensionality(data)

        if labels is not None:
            importance_scores = self.selector.rank_features(data, labels)
            data = self.selector.prune_features(data, importance_scores)

            self.validator.detect_leakage(data, labels)

        self.validator.validate_stationarity(data)
        self.validator.handle_outliers(data)
        self.validator.monitor_drift(data)

        return data