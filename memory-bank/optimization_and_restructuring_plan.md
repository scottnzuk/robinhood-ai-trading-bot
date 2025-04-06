# Optimization & Restructuring Plan

---

## Causes of Rapid Growth

- Accidental commits of large data files, virtual environments, caches
- Inclusion of third-party packages or submodules
- Generated files, logs, checkpoints

---

## Cleanup Actions

- Update `.gitignore` to exclude data, `.venv`, logs, caches
- Remove committed large files with `git rm --cached`
- Use `git filter-repo` or BFG to purge history

---

## Modular Project Structure

- `src/ai_trading_framework/`
  - `models/`
  - `data/`
  - `training/`
  - `execution/`
  - `utils/`
- `scripts/`
- `tests/`
- `memory-bank/`

---

## Maintainability Improvements

- Modular, decoupled design
- Clear interfaces and docstrings
- Unit tests and CI
- Automated linting and formatting

---

## Cross-Platform Setup

- Provide `requirements.txt` and `environment.yml`
- Add `Makefile` or CLI scripts for install, test, train, run

---

## Next Steps

- Clean repo history
- Refactor code into modules
- Improve documentation
- Automate testing and deployment