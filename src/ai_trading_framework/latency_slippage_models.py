"""
Latency and Slippage Modeling Framework
Implements configurable stochastic and historical models with global and per-asset overrides.
"""

import json
import numpy as np
from typing import Dict, Any, Optional


class BaseLatencyModel:
    def sample(self, asset: str = None) -> float:
        raise NotImplementedError


class NormalLatencyModel(BaseLatencyModel):
    def __init__(self, mean_ms: float, std_ms: float):
        self.mean = mean_ms
        self.std = std_ms

    def sample(self, asset: str = None) -> float:
        return max(0, np.random.normal(self.mean, self.std))


class HistoricalLatencyModel(BaseLatencyModel):
    def __init__(self, samples: np.ndarray):
        self.samples = samples

    def sample(self, asset: str = None) -> float:
        return float(np.random.choice(self.samples))


class BaseSlippageModel:
    def sample(self, asset: str = None) -> float:
        raise NotImplementedError


class LognormalSlippageModel(BaseSlippageModel):
    def __init__(self, mu: float, sigma: float):
        self.mu = mu
        self.sigma = sigma

    def sample(self, asset: str = None) -> float:
        return np.random.lognormal(self.mu, self.sigma)


class HistoricalSlippageModel(BaseSlippageModel):
    def __init__(self, samples: np.ndarray):
        self.samples = samples

    def sample(self, asset: str = None) -> float:
        return float(np.random.choice(self.samples))


class LatencySlippageModelFactory:
    def __init__(self, config: Dict[str, Any]):
        self.latency_models: Dict[str, BaseLatencyModel] = {}
        self.slippage_models: Dict[str, BaseSlippageModel] = {}

        # Global defaults
        global_lat = config.get('latency_model', {}).get('global', {})
        global_slip = config.get('slippage_model', {}).get('global', {})

        self.default_latency = self._create_latency_model(global_lat)
        self.default_slippage = self._create_slippage_model(global_slip)

        # Per-asset overrides
        for asset, lat_cfg in config.get('latency_model', {}).get('per_asset', {}).items():
            self.latency_models[asset] = self._create_latency_model(lat_cfg)

        for asset, slip_cfg in config.get('slippage_model', {}).get('per_asset', {}).items():
            self.slippage_models[asset] = self._create_slippage_model(slip_cfg)

    def _create_latency_model(self, cfg: Dict[str, Any]) -> BaseLatencyModel:
        if cfg.get('type') == 'normal':
            return NormalLatencyModel(cfg['mean_ms'], cfg['std_ms'])
        elif cfg.get('type') == 'historical':
            samples = np.loadtxt(cfg['source'], delimiter=',')
            return HistoricalLatencyModel(samples)
        else:
            # Default no latency
            return NormalLatencyModel(0, 0)

    def _create_slippage_model(self, cfg: Dict[str, Any]) -> BaseSlippageModel:
        if cfg.get('type') == 'lognormal':
            return LognormalSlippageModel(cfg['mu'], cfg['sigma'])
        elif cfg.get('type') == 'historical':
            samples = np.loadtxt(cfg['source'], delimiter=',')
            return HistoricalSlippageModel(samples)
        else:
            # Default no slippage
            return LognormalSlippageModel(0, 0)

    def sample_latency(self, asset: Optional[str] = None) -> float:
        model = self.latency_models.get(asset, self.default_latency)
        return model.sample(asset)

    def sample_slippage(self, asset: Optional[str] = None) -> float:
        model = self.slippage_models.get(asset, self.default_slippage)
        return model.sample(asset)