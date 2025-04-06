#!/usr/bin/env python3

import sys
import subprocess

MIN_PYTHON = (3, 8)

def check_python_version():
    if sys.version_info < MIN_PYTHON:
        print(f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ required, found {sys.version}")
        sys.exit(1)
    else:
        print(f"Python version OK: {sys.version}")

def check_package(pkg):
    try:
        __import__(pkg)
        print(f"Package '{pkg}' found.")
    except ImportError:
        print(f"Package '{pkg}' NOT found.")
        sys.exit(1)

def main():
    check_python_version()
    required_packages = ['numpy', 'torch', 'yaml']
    for pkg in required_packages:
        check_package(pkg)
    print("All environment checks passed.")

if __name__ == "__main__":
    main()