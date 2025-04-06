"""
Execution Metrics Logger
Logs per-order execution details in JSON format, supports real-time aggregation and post-trade analysis.
"""

import json
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime


class ExecutionMetricsLogger:
    def __init__(self, output_file: str):
        self.output_file = output_file
        self.lock = threading.Lock()
        self.aggregates = {
            "latency_ms": [],
            "slippage": []
        }

    def log_fill(self, data: Dict[str, Any]):
        """
        Log a single order fill event.
        """
        data['logged_at'] = datetime.utcnow().isoformat()
        line = json.dumps(data)

        with self.lock:
            with open(self.output_file, 'a') as f:
                f.write(line + '\n')

            # Update aggregates
            latency = data.get('latency_ms')
            slippage = data.get('slippage')
            if latency is not None:
                self.aggregates['latency_ms'].append(latency)
            if slippage is not None:
                self.aggregates['slippage'].append(slippage)

    def get_aggregates(self) -> Dict[str, Dict[str, float]]:
        """
        Return real-time aggregate statistics.
        """
        import numpy as np
        agg_stats = {}

        with self.lock:
            for key, values in self.aggregates.items():
                arr = np.array(values)
                if len(arr) == 0:
                    agg_stats[key] = {"mean": 0, "std": 0, "p95": 0}
                else:
                    agg_stats[key] = {
                        "mean": float(np.mean(arr)),
                        "std": float(np.std(arr)),
                        "p95": float(np.percentile(arr, 95))
                    }
        return agg_stats

    def load_all_logs(self) -> List[Dict[str, Any]]:
        """
        Load all logged fills from file.
        """
        fills = []
        with open(self.output_file, 'r') as f:
            for line in f:
                fills.append(json.loads(line))
        return fills

    def analyze_post_trade(self) -> Dict[str, Any]:
        """
        Placeholder for post-trade analysis logic.
        """
        fills = self.load_all_logs()
        # TODO: implement detailed analytics
        return {
            "total_fills": len(fills),
            "sample_fill": fills[0] if fills else {}
        }