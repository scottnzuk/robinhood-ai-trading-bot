## System Patterns - Updated 2025-04-10 16:25

### Architecture Patterns
- Optimized Package Structure:
  - Core modules for primary functionality
  - Specialized packages with clear responsibilities
  - Proper encapsulation with __init__.py exports
  - Consistent import patterns
  - Reduced duplication and improved cohesion

- Unified Trading Framework:
  - Strategy Framework with weighted signal combination
  - Risk Management System with position sizing
  - AI Trading Engine with dynamic prompts
  - Backtesting Framework for strategy validation
  - Anti-Gaming System with multiple protection strategies
- Native async-first, multi-exchange ingestion pipeline
- Modular plugin architecture with Pluggy
- Ensemble candle classification:
  - TA-Lib rule-based
  - Classic signals (MA, RSI) via Strategy Framework
  - Alpaca-LoRA LLaMA LLM (local)
  - Flan-T5 LLM (local)
  - Quantized phi model (pending)
- Advanced execution engine:
  - Adaptive sizing, iceberg, TWAP/VWAP
  - Behavioral noise, randomized timing, decoys
  - Multi-exchange sharding, rebate optimization
  - Circuit breakers, anomaly detection, threat ensemble
- Real-time monitoring with Prometheus and Grafana
- Deployment automation with scripts and CI/CD
- Memory Bank for persistent context and decisions

### Project Structure Pattern

**Pattern Name**: Modular Trading System Architecture

**Implementation**:
- Core functionality organized by domain (execution/risk/strategies)
- Strict separation between:
  - Trading infrastructure (src/execution)
  - Risk controls (src/risk_management)
  - AI components (src/models)
- Memory bank contains all non-code documentation
- Tests mirror source structure

**Benefits**:
- Reduces cognitive load through clear boundaries
- Enables parallel development
- Simplifies CI/CD pipeline configuration
- Facilitates regulatory compliance auditing

### Design Patterns
- Strategy pattern for modular trading signals and strategy composition
- Registry pattern for managing and combining multiple strategies
- Factory pattern for signal generation and strategy instantiation
- Template method pattern for strategy implementation
- Observer pattern for metrics and alerts
- Circuit breaker pattern for adaptive halts
- Ensemble pattern for multi-model voting and signal combination
- Decorator pattern for plugin hooks and strategy enhancement
- Adapter pattern for exchange integrations
- Command pattern for trade execution
- Repository pattern for historical data access in backtesting

### Integration Patterns
- Weighted ensemble for strategy signal combination
- Dynamic prompt generation based on market conditions
- Position sizing based on risk parameters and volatility
- Backtesting with realistic trade simulation
- Local model loading with explicit paths
- Hot-swappable ONNX models
- Quantized model support
- Multi-modal ensemble (rules + AI + classic)
- Continuous autonomous execution loop