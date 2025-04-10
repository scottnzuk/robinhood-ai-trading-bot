## Product Context - Updated 2025-04-10 15:54

### Overview
A fully autonomous, multi-exchange crypto trading system with:

- Unified Trading Framework:
  - Strategy Framework with weighted signal combination
  - Risk Management System with position sizing and risk controls
  - AI Trading Engine with dynamic prompts based on market conditions
  - Backtesting Framework for strategy validation on historical data
- Multi-model candle pattern recognition:
  - TA-Lib rule-based detection
  - Classic signals (MA, RSI) via Strategy Framework
  - Alpaca-LoRA LLaMA LLM (local, fine-tuned)
  - Flan-T5 fine-tuned LLM (local)
  - Quantized phi model (pending integration)
- Advanced execution engine:
  - Adaptive sizing, iceberg, TWAP/VWAP
  - Behavioral noise, decoys, randomized timing
  - Multi-exchange sharding, rebate optimization
  - Circuit breakers, anomaly detection, threat ensemble
- Modular plugin architecture with Pluggy
- Real-time monitoring, Prometheus metrics, Grafana dashboards
- Deployment automation, CI/CD, and environment setup scripts
- Memory Bank for persistent context and decision logs

### Key Features
- Modular, extensible architecture for trading strategies
- Comprehensive risk management with position sizing
- Dynamic AI prompts that adapt to market conditions
- Backtesting capabilities for strategy validation
- Fully async, scalable, and fault-tolerant
- Multi-layered anti-gaming and stealth tactics
- Ensemble of AI, rule-based, and classic signals
- Real-time adaptive threat mitigation
- Extensible with new models and strategies
- Designed for Apple Silicon with MPS acceleration
- Production-ready, continuously optimized

### Status
- Unified Trading Framework implemented and operational
- Core ingestion, analytics, execution operational
- Candle classification ensemble integrated
- Threat detection and circuit breakers active
- Backtesting system ready for strategy validation
- Deployment and monitoring in place
- Final tuning, testing, and model integration ongoing