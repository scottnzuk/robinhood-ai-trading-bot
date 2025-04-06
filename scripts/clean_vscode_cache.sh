#!/bin/bash
echo 'Cleaning VSCode workspace cache and Python caches...'

# Remove VSCode Python extension caches
rm -rf .vscode/.python* .vscode/__pycache__

# Remove common Python cache directories
rm -rf .mypy_cache/ .pytest_cache/

# Remove all __pycache__ folders recursively
find . -type d -name '__pycache__' -exec rm -rf {} +

echo 'Cleanup complete. Please restart VSCode and reload the language server.'