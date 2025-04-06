import numpy as np
import torch
import json
import os
from datetime import datetime

class Backtester:
    def __init__(self, model, data_loader, horizons=(10, 60, 240), device='cpu'):
        self.model = model
        self.data_loader = data_loader
        self.horizons = horizons
        self.device = device
        self.results_dir = "backtest_results"
        os.makedirs(self.results_dir, exist_ok=True)

    def walk_forward_validation(self, window_size=1000, step_size=100):
        results = []
        n_samples = len(self.data_loader)
        for start in range(0, n_samples - window_size, step_size):
            end = start + window_size
            train_data = self.data_loader.get_slice(0, end)
            test_data = self.data_loader.get_slice(end, end + step_size)

            # Placeholder: update model here
            # self.model.fit(train_data)

            metrics = self.evaluate(test_data)
            results.append(metrics)

        self.save_results(results, "walk_forward")
        return results

    def evaluate(self, data):
        self.model.eval()
        all_metrics = {h: [] for h in self.horizons}
        for batch_inputs, batch_targets, _ in data:
            with torch.no_grad():
                outputs = self.model(batch_inputs)
            for horizon in self.horizons:
                out = outputs[horizon]
                mean = out['mean'].cpu().numpy()
                log_var = out['log_var'].cpu().numpy()
                target = batch_targets[horizon].cpu().numpy()
                mse = np.mean((mean - target) ** 2)
                var = np.exp(log_var)
                sharpes = mean / (np.sqrt(var) + 1e-8)
                all_metrics[horizon].append({'mse': mse, 'sharpe': np.mean(sharpes)})
        agg_metrics = {}
        for horizon in self.horizons:
            mse = np.mean([m['mse'] for m in all_metrics[horizon]])
            sharpe = np.mean([m['sharpe'] for m in all_metrics[horizon]])
            agg_metrics[horizon] = {'mse': mse, 'sharpe': sharpe}
        return agg_metrics

    def monte_carlo_simulation(self, base_data, n_sims=100):
        sim_results = []
        for _ in range(n_sims):
            noise = np.random.normal(0, 1, base_data.shape)
            sim_data = base_data + noise * 0.01
            metrics = self.evaluate(sim_data)
            sim_results.append(metrics)
        self.save_results(sim_results, "monte_carlo")
        return sim_results

    def robustness_checks(self, data):
        # Placeholder: adversarial perturbations, drift detection, etc.
        pass

    def save_results(self, results, label):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.results_dir}/{label}_{timestamp}.json"
        with open(filename, "w") as f:
            json.dump(results, f, indent=2)