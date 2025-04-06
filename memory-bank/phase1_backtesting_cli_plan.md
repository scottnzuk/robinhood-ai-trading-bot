# Implementation Phase 1: Backtesting CLI & Config Support

## Goals
- Add CLI entry point for backtesting
- Support YAML/JSON config files
- Allow CLI overrides
- Export results to JSON/CSV
- Modularize agent interface

---

## Steps

### 1. CLI Script `run_backtest.py`
- Use `argparse` to parse:
  - `--config` path to config file
  - `--output` path for results
  - Optional overrides (symbol, steps, initial_cash, etc.)
- Load config file
- Merge CLI overrides
- Initialize `BacktestOrchestrator`
- Run async backtest
- Save results to output file

### 2. Config Loader
- Support YAML (`pyyaml`) or JSON
- Validate required fields
- Nested parameters for agents, data, simulation

### 3. Results Export
- Save final metrics as JSON
- Optionally save trade history as CSV
- Prepare for visualization scripts

### 4. Modular Agent Interface
- Abstract base class for RL agents
- Allow plug-in of different agent types in future

---

## Notes
- No Docker usage
- Cross-platform compatible
- Minimal dependencies beyond existing ones

---

*Generated 2025-04-06 05:17 UTC+1 by Roo Code Mode*