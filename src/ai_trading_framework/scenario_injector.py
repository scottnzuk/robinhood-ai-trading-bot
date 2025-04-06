"""
Scenario Injection and Deterministic Replay Framework
Supports scripted/randomized scenarios with reproducibility.
"""

import json
import random
from typing import Dict, Any, Optional


class ScenarioInjector:
    def __init__(self, scenario_config: Dict[str, Any], seed: Optional[int] = None):
        self.config = scenario_config
        self.seed = seed if seed is not None else random.randint(0, 1 << 30)
        self.random = random.Random(self.seed)
        self.current_time = 0
        self.events = self._parse_events(scenario_config.get('events', []))

    def _parse_events(self, events_config):
        """
        Parse scenario event configs into internal format.
        """
        parsed = []
        for evt in events_config:
            evt_copy = evt.copy()
            evt_copy['time'] = evt.get('time', 0)
            parsed.append(evt_copy)
        parsed.sort(key=lambda e: e['time'])
        return parsed

    def reset(self):
        """
        Reset replay to initial state.
        """
        self.random.seed(self.seed)
        self.current_time = 0

    def inject_events(self, current_time: float) -> Dict[str, Any]:
        """
        Inject scenario events at the given simulation time.
        Returns dict of injected parameters.
        """
        injected = {}
        while self.events and self.events[0]['time'] <= current_time:
            evt = self.events.pop(0)
            injected.update(evt.get('params', {}))
        self.current_time = current_time
        return injected

    def randomize_param(self, param_name: str, distribution: Dict[str, Any]) -> float:
        """
        Generate randomized parameter based on distribution spec.
        """
        dist_type = distribution.get('type')
        if dist_type == 'uniform':
            return self.random.uniform(distribution['min'], distribution['max'])
        elif dist_type == 'normal':
            return self.random.gauss(distribution['mean'], distribution['std'])
        elif dist_type == 'choice':
            return self.random.choice(distribution['choices'])
        else:
            raise ValueError(f"Unsupported distribution type: {dist_type}")

    def save_metadata(self, path: str):
        """
        Save scenario seed and config for deterministic replay.
        """
        meta = {
            'seed': self.seed,
            'config': self.config
        }
        with open(path, 'w') as f:
            json.dump(meta, f, indent=2)

    @staticmethod
    def load_metadata(path: str) -> 'ScenarioInjector':
        """
        Load scenario injector from saved metadata.
        """
        with open(path, 'r') as f:
            meta = json.load(f)
        return ScenarioInjector(meta['config'], meta['seed'])