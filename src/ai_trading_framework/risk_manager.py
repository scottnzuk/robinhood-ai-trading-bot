from typing import Dict, Any, List


class RiskManager:
    """
    Advanced risk management module.
    Handles position sizing, stop-loss/take-profit optimization, and portfolio risk aggregation.
    Uses probabilistic models and adaptive controls.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize with risk parameters and portfolio state.
        """
        self.config = config
        self.portfolio = {}  # Placeholder for portfolio holdings and stats

    def dynamic_position_size(
        self,
        signal_confidence: float,
        volatility: float,
        exposure: float,
        account_balance: float = None,
        risk_tolerance: float = None
    ) -> float:
        """
        Calculate position size using Kelly Criterion, volatility, exposure,
        and optionally account balance and risk tolerance.

        Args:
            signal_confidence (float): Model confidence score (0-1).
            volatility (float): Current market volatility.
            exposure (float): Current portfolio exposure (0-1).
            account_balance (float, optional): Total account balance.
            risk_tolerance (float, optional): Max risk per trade as fraction of balance.

        Returns:
            float: Position size as fraction of account or normalized (0-1).
        """
        p = signal_confidence
        q = 1 - p
        b = 1  # Reward/risk ratio, can be parameterized

        kelly_fraction = (b * p - q) / b

        # Adjust for volatility (scale down if high volatility)
        vol_adjustment = max(0.1, min(1.0, 0.2 / (volatility + 1e-6)))  # scale between 0.1 and 1

        # Adjust for current exposure (reduce if already heavily exposed)
        exposure_adjustment = max(0.1, 1.0 - exposure)

        size = kelly_fraction * vol_adjustment * exposure_adjustment

        # Cap position size between 0 and 1
        size = max(0.0, min(1.0, size))

        # If account_balance and risk_tolerance provided, scale accordingly
        if account_balance is not None and risk_tolerance is not None:
            dollar_risk = account_balance * risk_tolerance
            # Assume stop distance is proportional to volatility
            stop_distance = volatility * 2  # can be tuned
            if stop_distance > 0:
                size_in_dollars = dollar_risk / stop_distance
                normalized_size = size_in_dollars / account_balance
                size = min(size, normalized_size)

        return size

    def optimize_stops(
        self,
        price_history: List[float],
        rl_model: Any = None,
        confidence_score: float = None,
        market_volatility: float = None
    ) -> Dict:
        """
        Optimize stop-loss and take-profit using ATR, adaptive scaling based on confidence,
        and optionally RL-based exits.

        Args:
            price_history (List[float]): Recent price history.
            rl_model (Any, optional): RL model for stop overrides.
            confidence_score (float, optional): Model confidence score (0-1).
            market_volatility (float, optional): Current market volatility.

        Returns:
            Dict: Dict with 'stop_loss' and 'take_profit' levels.
        """
        import numpy as np

        atr_period = self.config.get("atr_period", 14)
        price_array = np.array(price_history[-atr_period:])

        if len(price_array) < atr_period:
            atr = np.std(price_array)  # fallback
        else:
            high = price_array
            low = price_array
            close = price_array
            tr = np.maximum(high[1:] - low[1:], np.abs(high[1:] - close[:-1]), np.abs(low[1:] - close[:-1]))
            atr = np.mean(tr)

        # Base stop-loss and take-profit multipliers
        stop_mult = 2.0
        tp_mult = 3.0

        # Adjust based on confidence score if provided
        if confidence_score is not None:
            # Wider stops for higher confidence, tighter for low
            stop_scale = 1.0 + (confidence_score - 0.5)  # 0.5 -> 1.0, 1.0 -> 1.5, 0.0 -> 0.5
            stop_scale = max(0.5, min(1.5, stop_scale))
            stop_mult *= stop_scale
            tp_mult *= stop_scale

        # Optionally adjust further based on market volatility
        if market_volatility is not None:
            vol_scale = max(0.5, min(1.5, 0.2 / (market_volatility + 1e-6)))
            stop_mult *= vol_scale
            tp_mult *= vol_scale

        stop_loss = -stop_mult * atr
        take_profit = tp_mult * atr

        # If RL model is provided, override with RL policy (placeholder)
        if rl_model is not None:
            try:
                rl_result = rl_model.predict(price_history)
                stop_loss = rl_result.get("stop_loss", stop_loss)
                take_profit = rl_result.get("take_profit", take_profit)
            except Exception:
                pass

        return {"stop_loss": stop_loss, "take_profit": take_profit}

    def monte_carlo_simulation(self, current_price: float, volatility: float, horizon: int = 100) -> List[float]:
        """
        Run Monte Carlo simulations to model future price scenarios.
        """
        import numpy as np

        dt = 1 / 252  # daily steps
        n_paths = 1000
        prices = []

        for _ in range(n_paths):
            price = current_price
            path = [price]
            for _ in range(horizon):
                shock = np.random.normal(0, volatility * np.sqrt(dt))
                price = price * np.exp(shock)
                path.append(price)
            prices.append(path[-1])

        return prices

    def calculate_cvar(self, pnl_distribution: List[float], alpha: float = 0.05) -> float:
        """
        Calculate Conditional Value at Risk (CVaR) from PnL distribution.
        """
        import numpy as np

        sorted_pnl = np.sort(pnl_distribution)
        index = int(alpha * len(sorted_pnl))
        cvar = np.mean(sorted_pnl[:index]) if index > 0 else sorted_pnl[0]

        return cvar

    def aggregate_portfolio_risk(self) -> Dict:
        """
        Aggregate total portfolio risk, exposure, and compliance status.
        """
        total_exposure = 0.0
        weighted_volatility = 0.0
        total_value = 0.0

        for asset, info in self.portfolio.items():
            exposure = info.get("exposure", 0.0)
            volatility = info.get("volatility", 0.0)
            value = info.get("value", 0.0)

            total_exposure += exposure
            weighted_volatility += volatility * value
            total_value += value

        avg_volatility = weighted_volatility / total_value if total_value > 0 else 0.0

        compliance = total_exposure <= self.config.get("max_exposure", 1.0)

        return {
            "total_exposure": total_exposure,
            "avg_volatility": avg_volatility,
            "compliance": compliance
        }

    def update_portfolio(self, fills: List[Dict]):
        """
        Update portfolio holdings based on executed trades.
        """
        for fill in fills:
            asset = fill.get("asset")
            qty = fill.get("quantity", 0)
            price = fill.get("price", 0)
            side = fill.get("side", "buy")

            if asset not in self.portfolio:
                self.portfolio[asset] = {"exposure": 0, "value": 0, "volatility": 0}

            position = self.portfolio[asset]

            if side == "buy":
                position["exposure"] += qty
                position["value"] += qty * price
            elif side == "sell":
                position["exposure"] -= qty
                position["value"] -= qty * price

            # Prevent negative exposure/value
            position["exposure"] = max(0, position["exposure"])
            position["value"] = max(0, position["value"])