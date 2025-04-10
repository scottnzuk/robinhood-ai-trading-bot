# Fix Plan for build.py PyInstaller Issue

## Detected Problem
- Invalid code: `PyInstaller.__main__`
- Pylance cannot resolve `PyInstaller.__main__`
- This is not a valid import or usage.

## Root Cause
- `PyInstaller.__main__` is a module, not an attribute.
- Proper usage requires importing `run` from `PyInstaller.__main__`.

## Fix Steps
1. Replace `PyInstaller.__main__` with:
   ```python
   from PyInstaller.__main__ import run
   ```
2. If the goal is to invoke PyInstaller programmatically, call:
   ```python
   run([<args>])
   ```
3. Add example usage or wrap in a function.
4. Add error handling.
5. Document the change.

## Next Step
- Apply the fix to `build.py`.
- Explain the fix.
- Pass to Architect mode for further planning.