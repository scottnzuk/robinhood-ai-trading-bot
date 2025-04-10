"""My Robin Stocks Extensions

This package safely extends the original robin_stocks library.
Place all your custom wrappers, patches, and new features here.
"""

# Example: import original modules
import robin_stocks.robinhood as rh
import robin_stocks.gemini as gm
import robin_stocks.tda as tda

# You can import specific functions or classes as needed
# from robin_stocks.robinhood import orders, authentication, account

# Example of a simple wrapper function
def my_get_account_info():
    """Example wrapper calling original function."""
    return rh.account.load_phoenix_account()

# Extend or override more functions in separate modules