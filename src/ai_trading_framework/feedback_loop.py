"""
Feedback Loop Module
---------------------

Logs trades, monitors performance, and triggers model retraining.

"""

def log_trade(trade_details):
    """
    Log executed trade details.

    Args:
        trade_details (dict): Info about the executed trade.
    """
    # Placeholder: print or write to database/file
    print("Trade logged:", trade_details)

def analyze_performance(trade_history):
    """
    Analyze historical trades to compute performance metrics.

    Args:
        trade_history (list of dict): List of trade logs.

    Returns:
        dict: Performance metrics.
    """
    num_trades = len(trade_history)
    profit = sum(t.get("profit", 0) for t in trade_history)
    win_trades = [t for t in trade_history if t.get("profit", 0) > 0]
    win_rate = len(win_trades) / num_trades if num_trades else 0

    return {
        "total_trades": num_trades,
        "total_profit": profit,
        "win_rate": win_rate,
    }

def trigger_retraining(performance_metrics):
    """
    Decide whether to trigger model retraining.

    Args:
        performance_metrics (dict): Output from analyze_performance.

    Returns:
        bool: True if retraining should be triggered.
    """
    if performance_metrics.get("win_rate", 1) < 0.5:
        print("Triggering model retraining due to low win rate.")
        return True
    return False