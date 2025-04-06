#!/usr/bin/env python3

import subprocess
import sys
import json
import shutil

def run_pip_audit(output_json="security_report.json"):
    if not shutil.which("pip-audit"):
        print("pip-audit not installed. Please install via 'pip install pip-audit'")
        sys.exit(1)
    print("Running pip-audit...")
    result = subprocess.run(["pip-audit", "-f", "json"], capture_output=True, text=True)
    if result.returncode != 0:
        print("pip-audit failed.")
        print(result.stderr)
        sys.exit(1)
    try:
        audit_data = json.loads(result.stdout)
    except json.JSONDecodeError:
        print("Failed to parse pip-audit output.")
        sys.exit(1)
    with open(output_json, 'w') as f:
        json.dump(audit_data, f, indent=2)
    print(f"Security report saved to {output_json}")

def main():
    run_pip_audit()

if __name__ == "__main__":
    main()