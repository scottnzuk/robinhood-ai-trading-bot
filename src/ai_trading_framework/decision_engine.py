"""
Decision Engine Module
----------------------

Applies portfolio constraints, risk management, and generates final trade decisions.

"""

def make_decision(signal_info, portfolio_state):
    """
    Decide on trade action based on signals and portfolio.

    Args:
        signal_info (dict): Output from signal generator.
        portfolio_state (dict): Current holdings, risk metrics.

    Returns:
        dict: Decision details including action and sizing.
    """
    base_signal = signal_info.get("signal", "hold")
    risk_level = portfolio_state.get("risk_level", "medium")
    exposure = portfolio_state.get("exposure", 0.5)  # 0 to 1

    # Example risk overlay
    if risk_level == "high" and exposure > 0.8:
        action = "reduce"
    elif risk_level == "low" and exposure < 0.2:
        action = "increase"
    else:
        action = base_signal

    # Example position sizing
    if action == "buy":
        size = min(1.0 - exposure, 0.1)  # max 10% increment
    elif action == "sell":
        size = min(exposure, 0.1)        # max 10% decrement
    elif action == "reduce":
        size = min(exposure, 0.2)        # reduce by up to 20%
    elif action == "increase":
        size = min(1.0 - exposure, 0.2)  # increase by up to 20%
    else:
        size = 0.0

    return {
        "action": action,
        "size": size,
        "final_signal": base_signal,
        "risk_level": risk_level,
        "exposure": exposure,
    }