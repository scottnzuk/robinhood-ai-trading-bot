#!/usr/bin/env python3

import subprocess
import os
import shutil
import sys
import hashlib

def run_env_check():
    print("Running environment check...")
    result = subprocess.run([sys.executable, "env_check.py"])
    if result.returncode != 0:
        print("Environment check failed.")
        sys.exit(1)

def clean_build():
    print("Cleaning previous builds...")
    for folder in ["dist", "build", "__pycache__"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
    if os.path.exists("app.zip"):
        os.remove("app.zip")
    if os.path.exists("app.tar.gz"):
        os.remove("app.tar.gz")

def build_with_pyinstaller():
    try:
        from PyInstaller.__main__ import run
    except ImportError:
        print("PyInstaller not installed, skipping binary build.")
        return False
    print("Building standalone executable with PyInstaller...")
    run([
        'run_backtest.py',
        '--onefile',
        '--name', 'ai_trading_bot'
    ])
    return True

def package_zip():
    print("Packaging source files into app.zip...")
    shutil.make_archive("app", 'zip', ".")

def generate_checksum(file_path):
    print(f"Generating SHA256 checksum for {file_path}...")
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    checksum = sha256.hexdigest()
    with open(file_path + ".sha256", 'w') as out:
        out.write(checksum)
    print(f"Checksum saved to {file_path}.sha256")

def main():
    run_env_check()
    clean_build()
    built = build_with_pyinstaller()
    if not built:
        package_zip()
        generate_checksum("app.zip")
    else:
        exe_path = os.path.join("dist", "ai_trading_bot")
        if sys.platform == "win32":
            exe_path += ".exe"
        generate_checksum(exe_path)
    print("Build complete.")

if __name__ == "__main__":
    main()