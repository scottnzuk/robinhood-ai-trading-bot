# My Robin Stocks Extensions

This package is designed to **safely extend and customize** the [robin_stocks](https://github.com/jmfernandes/robin_stocks) library **without modifying the original cloned repository**.

---

## Why use this?

- **Keep the upstream `robin_stocks` repo pristine** for easy updates or re-cloning.
- **Add new features, bug fixes, or wrappers** without risk.
- **Override or patch existing API calls** in a clean, maintainable way.
- **Organize your own trading logic** separately from the vendor code.

---

## How to use

1. **Import your extension package instead of `robin_stocks` directly:**

```python
import my_robin_stocks_extensions as myrs

# Call your wrapper or extended functions
myrs.my_get_account_info()
```

2. **Add your own modules**

Create new files like `robinhood_wrappers.py`, `gemini_patches.py`, etc., inside this folder.

3. **Extend or override**

Wrap or override original functions:

```python
import robin_stocks.robinhood as rh

def my_custom_order(*args, **kwargs):
    # Add your logic here
    return rh.orders.order_buy_market(*args, **kwargs)
```

4. **Keep your changes safe**

Since this folder is outside the cloned repo, you can update or delete the original `robin_stocks` anytime without losing your work.

---

## Example structure

```
my_robin_stocks_extensions/
├── __init__.py
├── robinhood_wrappers.py
├── gemini_patches.py
├── tda_extensions.py
└── README.md
```

---

## Notes

- You can also create **subpackages** inside this folder if needed.
- Remember to update your imports to use your extensions.
- Follow best practices for packaging if you want to distribute or reuse this code.

---

## License

Your own license here.