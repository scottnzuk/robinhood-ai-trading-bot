# Workspace Diagnostics Review and Remediation Plan

---

## A. Dependency Management

- **Issues:**
  - `Import "yaml" could not be resolved`
  - `Import "ray"` and `ray.tune` missing

- **Actions:**
  - Add `pyyaml` and `ray` to `requirements.txt`
  - Verify virtual environment activation
  - Document environment setup

---

## B. Security Improvements

### 1. Hardcoded Credentials (`src/api/onepassword.py`)

- **Problem:** Secrets embedded in code
- **Fix:** Use environment variables or secret manager
- **Example:**

```python
import os
PASSWORD = os.getenv('ONEPASSWORD_SECRET')
```

---

### 2. Path Traversal (`run_backtest.py`)

- **Problem:** Unsanitized CLI args used in `open()` and `json.dump()`
- **Fix:** Validate and sanitize inputs
- **Example:**

```python
import os
filepath = os.path.abspath(user_input)
if not filepath.startswith(allowed_dir):
    raise ValueError("Invalid path")
```

---

### 3. Attribute Access on `None` or Primitives

- **Problem:** Possible `AttributeError`
- **Fix:** Add explicit checks

```python
if obj is not None:
    value = obj.attr
```

---

### 4. Unguarded `next()` Calls

- **Fix:**

```python
try:
    item = next(iterator)
except StopIteration:
    item = None
```

---

## C. Code Quality Improvements

- Replace `== None` with `is None`
- Refactor identical branches
- Remove redundant `close()` in context managers
- Add type hints and docstrings

---

## D. Testing & Validation

- Add unit tests for edge cases
- Use static analysis tools: `mypy`, `pylint`, `bandit`
- Integrate Snyk scans into CI/CD

---

## Next Steps

- Prioritize security fixes
- Update dependencies
- Refactor code style issues
- Validate with tests and static analysis