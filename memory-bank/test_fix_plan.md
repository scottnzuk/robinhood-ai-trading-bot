# Fix Plan: Hanging `test_auth_failure`

---

## Problem

- `test_auth_failure` hangs indefinitely if `TradingBot.run()` does not exit on failed login.
- No timeout wrapper on `await trading_bot.run()`.
- Expected `SystemExit` may not be raised promptly.

---

## Solution

1. **Add timeout to test**

```python
with pytest.raises(SystemExit):
    await asyncio.wait_for(trading_bot.run(), timeout=5.0)
```

2. **Verify `TradingBot.run()`**

- Should exit promptly on login failure.
- If it retries indefinitely, patch or mock retry logic in test.

3. **Optional**

- Patch `asyncio.sleep` to a no-op during test to avoid delays.
- Add logging or debug prints to confirm flow.

---

## Next Step

Update `tests/integration/test_trading_loop.py` accordingly.

---

*Generated 2025-04-06 05:27 UTC+1 by Roo Architect Mode*