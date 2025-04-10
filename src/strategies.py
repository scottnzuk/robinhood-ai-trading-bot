import pandas as pd

class MovingAverageCrossStrategy:
    def __init__(self, df: pd.DataFrame, short_window=20, long_window=50):
        self.df = df
        self.short_window = short_window
        self.long_window = long_window

    def generate_signals(self):
        df = self.df.copy()
        df['short_ma'] = df['close'].rolling(window=self.short_window, min_periods=1).mean()
        df['long_ma'] = df['close'].rolling(window=self.long_window, min_periods=1).mean()
        df['signal'] = 0
        df.loc[df['short_ma'] > df['long_ma'], 'signal'] = 1
        df.loc[df['short_ma'] < df['long_ma'], 'signal'] = -1
        return df[['signal']]

class RSIStrategy:
    def __init__(self, df: pd.DataFrame, period=14, overbought=70, oversold=30):
        self.df = df
        self.period = period
        self.overbought = overbought
        self.oversold = oversold

    def generate_signals(self):
        df = self.df.copy()
        delta = df['close'].diff()
        gain = delta.clip(lower=0).rolling(window=self.period, min_periods=1).mean()
        loss = -delta.clip(upper=0).rolling(window=self.period, min_periods=1).mean()
        rs = gain / (loss + 1e-9)
        df['rsi'] = 100 - (100 / (1 + rs))
        df['signal'] = 0
        df.loc[df['rsi'] > self.overbought, 'signal'] = -1
        df.loc[df['rsi'] < self.oversold, 'signal'] = 1
        return df[['signal']]