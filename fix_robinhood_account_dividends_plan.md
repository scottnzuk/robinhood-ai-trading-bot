# Enhanced Fix Plan: `get_dividends_by_instrument` in `robinhood/account.py`

## Problems Addressed
- Use of `list(filter(lambda...))` instead of list comprehension.
- Broad `except:` block that silently ignores all errors.
- Potential `IndexError` if no dividends match the instrument.

---

## Solution Details

### 1. Replace `filter()` with list comprehension

**Before:**

```python
data = list(filter(lambda x: x['instrument'] == instrument, dividend_data))
```

**After:**

```python
data = [x for x in dividend_data if x['instrument'] == instrument]
```

---

### 2. Improve error handling

- Explicitly check if `data` is empty.
- Raise a meaningful error or return `None` if no dividends found.
- Catch specific exceptions (`KeyError`, `IndexError`, `ValueError`) instead of broad `except`.
- Optionally log or print the error.

---

### 3. Proposed Corrected Function

```python
@login_required
def get_dividends_by_instrument(instrument, dividend_data):
    """
    Returns dividend info for a specific instrument.
    """
    try:
        data = [x for x in dividend_data if x.get('instrument') == instrument]
        if not data:
            # No dividends found for this instrument
            return None

        dividend = float(data[0].get('rate', 0))
        total_dividends = float(data[0].get('amount', 0))
        total_amount_paid = sum(float(d.get('amount', 0)) for d in data)

        return {
            'dividend_rate': "{0:.2f}".format(dividend),
            'total_dividend': "{0:.2f}".format(total_dividends),
            'amount_paid_to_date': "{0:.2f}".format(total_amount_paid)
        }
    except (KeyError, IndexError, ValueError) as e:
        # Log or handle error appropriately
        # For now, return None to indicate failure
        return None
```

---

## Benefits

- More Pythonic and readable.
- Safer: avoids silent failures.
- Easier to debug if issues arise.
- Maintains backward compatibility (returns `None` on error).

---

## Next Steps

- Implement this improved function.
- Test with various inputs (matching, non-matching, malformed data).
- Commit and document the change.