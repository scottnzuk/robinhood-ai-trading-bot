# Fix Plan: Properly Close Global `requests.Session` in `gemini/globals.py`

## Problem
- Global `SESSION = Session()` created at import time.
- Not explicitly closed, leading to Snyk warning: **Missing close for requests.Session**.
- Potential resource leak if interpreter exits without cleanup.

## Solution
- Add a cleanup function `close_session()` that calls `SESSION.close()`.
- Register this function with `atexit` to ensure cleanup on interpreter exit.
- Document this behavior.

## Implementation Steps
1. **Import `atexit`** module.
2. **Define cleanup function:**
   ```python
   def close_session():
       SESSION.close()
   ```
3. **Register cleanup:**
   ```python
   atexit.register(close_session)
   ```
4. **(Optional)**: Log or print when session is closed for debugging.
5. **Verify** no other issues exist in the module.

## Notes
- This approach maintains the global session pattern.
- Avoids refactoring all code to use context managers.
- Ensures resource cleanup without changing API.

---

## Next Steps
- Implement fix in `robin_stocks/robin_stocks/gemini/globals.py`.
- Commit changes.
- Pass to Architect mode for expansion of next steps.