# Robinhood AI Trading Bot

A sophisticated algorithmic trading system that combines technical analysis, AI-driven decision making, and robust risk management to automate trading on the Robinhood platform.

## Features

### Core Trading Framework
- **Strategy Registry**: Unified framework for combining multiple trading strategies
- **Risk Management**: Advanced position sizing and risk control system
- **AI Integration**: Dynamic AI prompts that adapt to market conditions
- **Backtesting**: Comprehensive system for testing strategies on historical data

### Trading Strategies
- **Technical Indicators**:
  - Moving Average Crossover
  - Relative Strength Index (RSI)
  - Support for custom technical strategies
- **AI-Powered Analysis**:
  - Market regime detection
  - Sentiment analysis
  - Pattern recognition
  - Adaptive decision making

### Risk Controls
- Position sizing based on account volatility
- Per-trade and daily drawdown limits
- Sector exposure management
- Stop-loss and take-profit automation
- Circuit breaker protection

### Performance Monitoring
- Real-time performance metrics
- Trade history logging
- Equity curve visualization
- Risk-adjusted return calculations

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/robinhood-ai-trading-bot.git
cd robinhood-ai-trading-bot

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your Robinhood credentials and API keys
```

## Usage

### Live Trading

```bash
# Run in demo mode (no real trades)
python src/main.py --demo-mode

# Run with specific logging level
python src/main.py --log-level DEBUG

# Limit maximum trades per day
python src/main.py --max-trades 5
```

### Backtesting

```bash
# Basic backtest with default settings
python src/main.py --backtest

# Backtest specific symbols
python src/main.py --backtest --symbols AAPL,MSFT,GOOGL

# Backtest with date range
python src/main.py --backtest --start-date 2023-01-01 --end-date 2023-12-31

# Backtest with specific strategies
python src/main.py --backtest --strategies ma_cross,rsi,ai

# Customize risk parameters
python src/main.py --backtest --max-position 0.03 --max-risk 0.01
```

## Project Structure

```
robinhood-ai-trading-bot/
├── data/                  # Data storage
│   ├── historical/        # Historical price data
│   └── trades/            # Trade history logs
├── results/               # Backtest results
├── src/                   # Source code
│   ├── ai_trading_engine.py   # AI trading components
│   ├── backtesting.py         # Backtesting framework
│   ├── circuit_breaker.py     # Circuit breaker protection
│   ├── config.py              # Configuration settings
│   ├── exceptions.py          # Custom exceptions
│   ├── main.py                # Main application entry point
│   ├── risk_management.py     # Risk management system
│   ├── strategy_framework.py  # Strategy framework
│   ├── validation.py          # Data validation
│   ├── api/                   # API clients
│   └── utils/                 # Utility functions
└── tests/                 # Test suite
```

## Adding New Strategies

To add a new trading strategy:

1. Create a class that inherits from `Strategy`, `TechnicalStrategy`, or `AIStrategy`
2. Implement the `generate_signals` method
3. Register your strategy with the `StrategyRegistry`

Example:

```python
from src.strategy_framework import TechnicalStrategy, Signal, SignalType

class BollingerBandStrategy(TechnicalStrategy):
    def __init__(self, window=20, num_std=2):
        super().__init__({"window": window, "num_std": num_std})
        self.window = window
        self.num_std = num_std
    
    def generate_signals(self, data):
        signals = []
        # Implementation here
        return signals

# In your main code:
registry = StrategyRegistry()
bb_strategy = BollingerBandStrategy()
registry.register(bb_strategy, weight=0.4)
```

## Risk Management Configuration

Customize risk parameters by modifying the `RiskParameters` class:

```python
from src.risk_management import RiskParameters

risk_params = RiskParameters(
    max_position_size=0.05,  # 5% of portfolio per position
    max_portfolio_risk=0.02,  # 2% daily risk
    max_symbol_risk=0.01,    # 1% risk per symbol
    max_sector_risk=0.20,    # 20% exposure to any sector
    stop_loss_pct=0.05,      # 5% stop loss
    take_profit_pct=0.10     # 10% take profit
)
```

## License

MIT

## Disclaimer

This software is for educational purposes only. Use at your own risk. Trading involves risk of financial loss. Past performance is not indicative of future results.
