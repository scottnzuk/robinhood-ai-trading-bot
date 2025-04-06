"""
Multi-Factor Signal Generation Module
Combines engineered features into composite trading signals.
"""

import numpy as np

class SignalGenerator:
    def __init__(self, config=None):
        self.config = config or {}

    def generate_signals(self, features):
        """Generate multi-factor signals from features."""
        weights = self.config.get("weights")
        if weights is None:
            weights = np.ones(features.shape[1])
        signals = np.dot(features, weights)
        threshold = self.config.get("threshold", 0)
        return (signals > threshold).astype(int)