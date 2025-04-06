#!/usr/bin/env python3

import argparse
import asyncio
import json
import os
import sys
import yaml

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.ai_trading_framework.backtesting import BacktestOrchestrator
from src.ai_trading_framework.rl_agents.a3c import A3CAgent

def load_config(path):
    with open(path, 'r') as f:
        if path.endswith('.yaml') or path.endswith('.yml'):
            return yaml.safe_load(f)
        elif path.endswith('.json'):
            return json.load(f)
        else:
            raise ValueError("Unsupported config format: use .yaml/.yml or .json")

def merge_overrides(config, args):
    # Override config fields with CLI args if provided
    if args.symbol:
        config['symbol'] = args.symbol
    if args.timeframe:
        config['timeframe'] = args.timeframe
    if args.steps:
        config['steps'] = args.steps
    if args.initial_cash:
        config['initial_cash'] = args.initial_cash
    return config

async def main():
    parser = argparse.ArgumentParser(description="Run AI Trading Backtest")
    parser.add_argument('--config', '-c', required=True, help='Path to YAML or JSON config file')
    parser.add_argument('--output', '-o', default='backtest_results.json', help='Output results JSON file')
    parser.add_argument('--symbol', help='Override symbol')
    parser.add_argument('--timeframe', help='Override timeframe')
    parser.add_argument('--steps', type=int, help='Override number of steps')
    parser.add_argument('--initial_cash', type=float, help='Override initial cash amount')
    args = parser.parse_args()

    safe_base = os.path.abspath(os.getcwd())

    args.config = os.path.abspath(args.config)
    args.output = os.path.abspath(args.output)

    if os.path.commonpath([safe_base, args.config]) != safe_base:
        raise ValueError("Invalid config file path")

    if os.path.commonpath([safe_base, args.output]) != safe_base:
        raise ValueError("Invalid output file path")

    config = load_config(args.config)
    config = merge_overrides(config, args)

    # Initialize agent
    agent_cfg = config.get('agent', {})
    env_name = agent_cfg.get('env_name', 'CartPole-v1')
    agent = A3CAgent(env_name=env_name, config=agent_cfg)

    orchestrator = BacktestOrchestrator(agent, config, initial_cash=config.get('initial_cash', 10000))
    results = await orchestrator.run(
        symbol=config.get('symbol', 'BTC/USDT'),
        timeframe=config.get('timeframe', '1m'),
        steps=config.get('steps', 1000)
    )

    # Save results
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {args.output}")

if __name__ == "__main__":
    asyncio.run(main())