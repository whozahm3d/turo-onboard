"""
setup.py — Run this ONCE before anything else.
In Jupyter: import subprocess; subprocess.run(["python", "setup.py"])
"""
import subprocess
import sys

steps = [
    ([sys.executable, "-m", "pip", "install", "playwright", "beautifulsoup4", "lxml"], "Installing packages"),
    (["playwright", "install", "chromium"], "Installing Chromium browser"),
]

for cmd, label in steps:
    print(f"\n[*] {label}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[✗] Failed:\n{result.stderr}")
        sys.exit(1)
    print(f"[✓] Done.")

print("\n✅ Setup complete. You can now run scraper.py.")
