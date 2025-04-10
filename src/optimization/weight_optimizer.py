"""
Strategy weight optimization based on backtesting results.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional
import random
from dataclasses import dataclass

from src.strategy_framework import Strategy, StrategyRegistry
from src.backtesting import BacktestResult


@dataclass
class OptimizationResult:
    """Results of strategy weight optimization"""
    weights: Dict[str, float]
    performance: Dict[str, float]
    iteration_history: List[Dict[str, Any]]


class WeightOptimizer:
    """
    Optimizes strategy weights based on backtesting results.
    
    This class implements various optimization methods:
    1. Grid Search - Exhaustive search through a specified subset of parameter space
    2. Random Search - Random sampling of parameter space
    3. Genetic Algorithm - Evolution-inspired optimization
    """
    
    def __init__(self, strategy_registry: StrategyRegistry, backtester: Any):
        """
        Initialize the weight optimizer.
        
        Args:
            strategy_registry: The strategy registry containing strategies to optimize
            backtester: The backtester to use for evaluating strategy performance
        """
        self.strategy_registry = strategy_registry
        self.backtester = backtester
        self.strategy_names = strategy_registry.list_strategies()
        self.best_weights = None
        self.best_performance = None
    
    def optimize_grid_search(
        self, 
        data: Dict[str, pd.DataFrame],
        steps: int = 5,
        metric: str = "sharpe_ratio",
        max_iterations: int = 100
    ) -> OptimizationResult:
        """
        Optimize weights using grid search.
        
        Args:
            data: Historical price data for backtesting
            steps: Number of steps between 0 and 1 for each weight
            metric: Performance metric to optimize ('sharpe_ratio', 'total_return', etc.)
            max_iterations: Maximum number of iterations to perform
            
        Returns:
            OptimizationResult with optimized weights and performance metrics
        """
        if len(self.strategy_names) == 0:
            return OptimizationResult({}, {}, [])
        
        # Generate weight combinations
        weight_values = np.linspace(0, 1, steps)
        
        # Track best results
        best_weights = {}
        best_performance = -float('inf') if metric != 'max_drawdown' else float('inf')
        history = []
        
        # Limit iterations for performance
        iterations = 0
        
        # Generate weight combinations
        for weights in self._generate_weight_combinations(weight_values, len(self.strategy_names)):
            if iterations >= max_iterations:
                break
                
            iterations += 1
            
            # Create weight dictionary
            weight_dict = {name: weight for name, weight in zip(self.strategy_names, weights)}
            
            # Skip if all weights are 0
            if sum(weight_dict.values()) == 0:
                continue
            
            # Normalize weights
            total = sum(weight_dict.values())
            weight_dict = {k: v/total for k, v in weight_dict.items()}
            
            # Run backtest with these weights
            performance = self._evaluate_weights(data, weight_dict, metric)
            
            # Track history
            history.append({
                "weights": weight_dict.copy(),
                "performance": performance
            })
            
            # Update best if better
            is_better = (
                (metric != 'max_drawdown' and performance > best_performance) or
                (metric == 'max_drawdown' and performance < best_performance)
            )
            
            if is_better:
                best_weights = weight_dict.copy()
                best_performance = performance
        
        # Save best results
        self.best_weights = best_weights
        self.best_performance = best_performance
        
        return OptimizationResult(
            weights=best_weights,
            performance={metric: best_performance},
            iteration_history=history
        )
    
    def optimize_random_search(
        self, 
        data: Dict[str, pd.DataFrame],
        iterations: int = 50,
        metric: str = "sharpe_ratio"
    ) -> OptimizationResult:
        """
        Optimize weights using random search.
        
        Args:
            data: Historical price data for backtesting
            iterations: Number of random weight combinations to try
            metric: Performance metric to optimize ('sharpe_ratio', 'total_return', etc.)
            
        Returns:
            OptimizationResult with optimized weights and performance metrics
        """
        if len(self.strategy_names) == 0:
            return OptimizationResult({}, {}, [])
        
        # Track best results
        best_weights = {}
        best_performance = -float('inf') if metric != 'max_drawdown' else float('inf')
        history = []
        
        for _ in range(iterations):
            # Generate random weights
            weight_dict = {name: random.random() for name in self.strategy_names}
            
            # Normalize weights
            total = sum(weight_dict.values())
            if total == 0:  # Avoid division by zero
                continue
                
            weight_dict = {k: v/total for k, v in weight_dict.items()}
            
            # Run backtest with these weights
            performance = self._evaluate_weights(data, weight_dict, metric)
            
            # Track history
            history.append({
                "weights": weight_dict.copy(),
                "performance": performance
            })
            
            # Update best if better
            is_better = (
                (metric != 'max_drawdown' and performance > best_performance) or
                (metric == 'max_drawdown' and performance < best_performance)
            )
            
            if is_better:
                best_weights = weight_dict.copy()
                best_performance = performance
        
        # Save best results
        self.best_weights = best_weights
        self.best_performance = best_performance
        
        return OptimizationResult(
            weights=best_weights,
            performance={metric: best_performance},
            iteration_history=history
        )
    
    def optimize_genetic_algorithm(
        self, 
        data: Dict[str, pd.DataFrame],
        population_size: int = 20,
        generations: int = 10,
        mutation_rate: float = 0.1,
        metric: str = "sharpe_ratio"
    ) -> OptimizationResult:
        """
        Optimize weights using a genetic algorithm.
        
        Args:
            data: Historical price data for backtesting
            population_size: Size of the population in each generation
            generations: Number of generations to evolve
            mutation_rate: Probability of mutation for each weight
            metric: Performance metric to optimize ('sharpe_ratio', 'total_return', etc.)
            
        Returns:
            OptimizationResult with optimized weights and performance metrics
        """
        if len(self.strategy_names) == 0:
            return OptimizationResult({}, {}, [])
        
        # Initialize population with random weights
        population = []
        for _ in range(population_size):
            weights = {name: random.random() for name in self.strategy_names}
            total = sum(weights.values())
            if total > 0:  # Avoid division by zero
                weights = {k: v/total for k, v in weights.items()}
                population.append(weights)
        
        # Track best results
        best_weights = {}
        best_performance = -float('inf') if metric != 'max_drawdown' else float('inf')
        history = []
        
        # Evolution loop
        for generation in range(generations):
            # Evaluate fitness for each individual
            fitness_scores = []
            for weights in population:
                performance = self._evaluate_weights(data, weights, metric)
                fitness_scores.append(performance)
                
                # Track history
                history.append({
                    "generation": generation,
                    "weights": weights.copy(),
                    "performance": performance
                })
                
                # Update best if better
                is_better = (
                    (metric != 'max_drawdown' and performance > best_performance) or
                    (metric == 'max_drawdown' and performance < best_performance)
                )
                
                if is_better:
                    best_weights = weights.copy()
                    best_performance = performance
            
            # Create next generation
            new_population = []
            
            # Elitism: keep the best individual
            if population:
                best_idx = np.argmax(fitness_scores) if metric != 'max_drawdown' else np.argmin(fitness_scores)
                new_population.append(population[best_idx])
            
            # Fill the rest with crossover and mutation
            while len(new_population) < population_size:
                # Selection (tournament selection)
                parent1 = self._tournament_selection(population, fitness_scores, metric)
                parent2 = self._tournament_selection(population, fitness_scores, metric)
                
                # Crossover
                child = self._crossover(parent1, parent2)
                
                # Mutation
                child = self._mutate(child, mutation_rate)
                
                # Add to new population
                new_population.append(child)
            
            # Replace old population
            population = new_population
        
        # Save best results
        self.best_weights = best_weights
        self.best_performance = best_performance
        
        return OptimizationResult(
            weights=best_weights,
            performance={metric: best_performance},
            iteration_history=history
        )
    
    def _evaluate_weights(
        self, 
        data: Dict[str, pd.DataFrame], 
        weights: Dict[str, float],
        metric: str
    ) -> float:
        """
        Evaluate a set of weights using backtesting.
        
        Args:
            data: Historical price data
            weights: Strategy weights to evaluate
            metric: Performance metric to return
            
        Returns:
            Performance metric value
        """
        # Set weights in registry
        for name, weight in weights.items():
            strategy = self.strategy_registry.get_strategy(name)
            if strategy:
                self.strategy_registry._weights[name] = weight
        
        # Run backtest
        result = self.backtester.run(data)
        
        # Extract metric
        if metric == "sharpe_ratio":
            return result.sharpe_ratio
        elif metric == "total_return":
            return result.total_return
        elif metric == "max_drawdown":
            return result.max_drawdown
        elif metric == "win_rate":
            return result.win_rate
        else:
            return result.sharpe_ratio  # Default
    
    def _generate_weight_combinations(self, weight_values: np.ndarray, num_strategies: int) -> List[List[float]]:
        """Generate all combinations of weights for grid search"""
        if num_strategies == 1:
            return [[w] for w in weight_values]
        
        result = []
        for w in weight_values:
            sub_combinations = self._generate_weight_combinations(weight_values, num_strategies - 1)
            for sub_comb in sub_combinations:
                result.append([w] + sub_comb)
        
        return result
    
    def _tournament_selection(
        self, 
        population: List[Dict[str, float]], 
        fitness_scores: List[float],
        metric: str
    ) -> Dict[str, float]:
        """Tournament selection for genetic algorithm"""
        # Select random individuals for tournament
        tournament_size = min(3, len(population))
        tournament_indices = random.sample(range(len(population)), tournament_size)
        
        # Find the best in the tournament
        if metric != 'max_drawdown':
            best_idx = max(tournament_indices, key=lambda i: fitness_scores[i])
        else:
            best_idx = min(tournament_indices, key=lambda i: fitness_scores[i])
            
        return population[best_idx]
    
    def _crossover(self, parent1: Dict[str, float], parent2: Dict[str, float]) -> Dict[str, float]:
        """Perform crossover between two parents"""
        child = {}
        for name in self.strategy_names:
            # 50% chance to inherit from each parent
            if random.random() < 0.5:
                child[name] = parent1.get(name, 0)
            else:
                child[name] = parent2.get(name, 0)
        
        # Normalize weights
        total = sum(child.values())
        if total > 0:
            child = {k: v/total for k, v in child.items()}
            
        return child
    
    def _mutate(self, individual: Dict[str, float], mutation_rate: float) -> Dict[str, float]:
        """Mutate an individual"""
        mutated = individual.copy()
        
        for name in self.strategy_names:
            # Apply mutation with probability mutation_rate
            if random.random() < mutation_rate:
                # Add random value between -0.2 and 0.2
                delta = (random.random() - 0.5) * 0.4
                mutated[name] = max(0, min(1, mutated.get(name, 0) + delta))
        
        # Normalize weights
        total = sum(mutated.values())
        if total > 0:
            mutated = {k: v/total for k, v in mutated.items()}
            
        return mutated
