# Integration Plan for `@timeout_async` and `@safe_mps_op` Decorators

## Overview
Integrate two new decorators to improve robustness and reliability:
- **`@timeout_async(seconds)`**: Enforces a timeout on async functions, raising `asyncio.TimeoutError` if exceeded.
- **`@safe_mps_op`**: Wraps Metal Performance Shaders (MPS) sensitive operations to catch and handle GPU-specific errors gracefully.

---

## 1. Decorator Implementations
- **Location:** `src/ai_trading_framework/mps_utils.py` or a new `src/utils/decorators.py`
- **Features:**
  - `timeout_async`: Use `asyncio.wait_for` internally.
  - `safe_mps_op`: Use try/except to catch MPS-related exceptions (e.g., `RuntimeError`, `torch.cuda`/`mps` errors), log, and optionally fallback or retry.

---

## 2. Target Integration Points

### a. `@timeout_async`
Apply to critical async functions prone to hanging:
- API calls (e.g., in `src/api/`)
- Async training loops (e.g., RL agents in `src/ai_trading_framework/rl_agents/`)
- Data fetching or streaming functions
- Any async function with external dependencies or long-running tasks

### b. `@safe_mps_op`
Apply to:
- Model training steps using MPS backend
- Inference calls on MPS
- Data transfer functions involving MPS
- Any function where MPS instability has been observed

---

## 3. Step-by-Step Integration Approach

1. **Implement Decorators**
   - Create or update `decorators.py` with both decorators.
   - Include docstrings and usage examples.

2. **Identify Candidate Functions**
   - Search for `async def` functions and GPU/MPS-related code.
   - Prioritize core trading loops, RL agent methods, and API calls.

3. **Apply Decorators**
   - Add `@timeout_async(seconds)` with sensible timeout values (e.g., 10-60s).
   - Add `@safe_mps_op` to GPU-sensitive functions.
   - Avoid redundant decoration or performance-critical tight loops.

4. **Testing**
   - Unit tests for decorators themselves.
   - Integration tests to verify timeouts trigger as expected.
   - Simulate MPS failures to verify graceful handling.
   - Regression tests on trading workflows.

5. **Documentation**
   - Update code comments.
   - Add decorator usage examples.
   - Log integration in Memory Bank (decisionLog.md, progress.md).

6. **Rollback Plan**
   - Keep decorator additions isolated (easy to remove).
   - Use feature flags if necessary.
   - Monitor for unintended side effects post-deployment.

---

## 4. Validation Strategy
- Run existing test suite.
- Add new tests for timeout and MPS error scenarios.
- Profile performance impact.
- Monitor logs during live runs.

---

## 5. Next Steps
- Implement decorators.
- Locate candidate functions.
- Apply decorators incrementally.
- Test thoroughly.
- Document and update Memory Bank.

---

*Generated on 2025-04-06 by Roo (Code Mode)*