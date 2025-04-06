import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional


@dataclass
class TradingObjectives:
    # Success metrics
    target_sharpe: float = 1.5
    max_drawdown: float = 0.15
    annualized_return: float = 0.2

    # Constraints
    max_leverage: float = 2.0
    regulatory_constraints: List[str] = field(default_factory=list)

    # Time horizon
    timeframe: str = "intraday"  # e.g., 'intraday', 'daily', 'weekly'
    intervals: List[str] = field(default_factory=lambda: ["1m", "5m"])

    # Additional metadata
    notes: Optional[str] = ""

    def to_dict(self) -> Dict:
        return asdict(self)

    def save_to_json(self, filepath: str):
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=4)

    @staticmethod
    def load_from_json(filepath: str) -> 'TradingObjectives':
        with open(filepath, "r") as f:
            data = json.load(f)
        return TradingObjectives(**data)

    def validate(self):
        assert 0 < self.target_sharpe, "Target Sharpe ratio must be positive."
        assert 0 <= self.max_drawdown <= 1, "Max drawdown must be between 0 and 1."
        assert 0 <= self.max_leverage, "Max leverage must be non-negative."
        assert self.timeframe in ["intraday", "daily", "weekly"], "Invalid timeframe."
        for interval in self.intervals:
            assert interval in ["1m", "5m", "15m", "1h", "1d"], f"Unsupported interval: {interval}"