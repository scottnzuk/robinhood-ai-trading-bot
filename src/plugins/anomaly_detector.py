from collections import defaultdict, deque
import math
from src.pluginspec import hookimpl

class AnomalyDetectorPlugin:
    def __init__(self, window_size=1000, z_threshold=3.0):
        self.window_size = window_size
        self.z_threshold = z_threshold
        self.prices = defaultdict(lambda: deque(maxlen=window_size))
        self.volumes = defaultdict(lambda: deque(maxlen=window_size))

    @hookimpl
    def pre_validate(self, trade_dict):
        symbol = trade_dict.get("symbol")
        price = float(trade_dict.get("price", 0))
        volume = float(trade_dict.get("volume", 0))

        # Update rolling windows
        self.prices[symbol].append(price)
        self.volumes[symbol].append(volume)

        # Compute stats
        def zscore(val, window):
            if len(window) < 30:
                return 0  # not enough data
            mean = sum(window) / len(window)
            std = math.sqrt(sum((x - mean) ** 2 for x in window) / len(window))
            if std == 0:
                return 0
            return abs((val - mean) / std)

        z_price = zscore(price, self.prices[symbol])
        z_volume = zscore(volume, self.volumes[symbol])

        if z_price > self.z_threshold:
            reason = f"Price anomaly z={z_price:.2f}"
            self.anomaly_alert(trade_dict, reason)
        if z_volume > self.z_threshold:
            reason = f"Volume anomaly z={z_volume:.2f}"
            self.anomaly_alert(trade_dict, reason)

        return trade_dict

    @hookimpl
    def anomaly_alert(self, trade_dict, reason):
        print(f"[ALERT] Anomaly detected: {reason} | Trade: {trade_dict}")