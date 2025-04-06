# Iterative Cleanup & Refactoring Execution Plan

_Last updated: 2025-04-06 07:05_

---

## Batch 1: Repository Cleanup
- Update `.gitignore` to exclude data, `.venv`, logs, caches, generated files.
- Remove committed large/binary files (`git rm --cached`).
- Commit message: **"Cleanup: update gitignore, remove large files"**
- Push changes.

---

## Batch 2: History Rewrite
- Use `git filter-repo` or BFG Repo-Cleaner to purge large files from git history.
- Commit message: **"Cleanup: purge large files from git history"**
- Push rewritten history.

---

## Batch 3: Modular Restructuring
- Organize code into:
  - `src/ai_trading_framework/` with submodules (`models/`, `data/`, `training/`, `execution/`, `utils/`)
  - `scripts/`
  - `tests/`
  - `memory-bank/`
- Commit message: **"Refactor: modularize project structure"**
- Push changes.

---

## Batch 4: Documentation & Interfaces
- Add clear docstrings and interface definitions.
- Improve README and internal documentation.
- Commit message: **"Docs: improve documentation and interfaces"**
- Push changes.

---


---

## Batch 2: Purge Large Files from Git History

Due to large binaries committed in the past, pushing is blocked by GitHub.

### Steps:
1. **Backup your repo** (optional but recommended).
2. Run:

```bash
git filter-repo --path .venv/lib/python3.10/site-packages/pyarrow/libarrow.1900.dylib --path .venv/lib/python3.10/site-packages/torch/lib/libtorch_cpu.dylib --invert-paths
```

3. **Force push** cleaned history:

```bash
git push --force
```

### Warning:
- This rewrites history. All collaborators **must re-clone** or reset.
- After this, large files will be removed permanently.

---

## Batch 5: Tooling & Automation
- Add or verify `requirements.txt` and `environment.yml`.
- Add Makefile or CLI scripts for install, test, train, run.
- Setup linting, formatting, CI configs.
- Commit message: **"Chore: add environment setup, automation scripts"**
- Push changes.

---

## Notes
- Each batch should be committed and pushed separately.
- Document changes thoroughly in commit messages.
- Verify functionality after each batch before proceeding.