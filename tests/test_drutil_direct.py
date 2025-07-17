#!/usr/bin/env python3
"""Test drutil command directly."""

import subprocess
import time

print("Testing drutil tray commands...")

# Test tray close
print("\n1. Closing tray...")
start = time.time()
try:
    result = subprocess.run(
        ["drutil", "-drive", "1", "tray", "close"],
        timeout=5.0,
        capture_output=True,
        text=True
    )
    elapsed = time.time() - start
    print(f"   Completed in {elapsed:.1f}s")
    print(f"   Return code: {result.returncode}")
    if result.stderr:
        print(f"   Stderr: {result.stderr}")
except subprocess.TimeoutExpired:
    print(f"   ❌ Timeout after 5 seconds!")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Wait a bit
time.sleep(2)

# Test tray open
print("\n2. Opening tray...")
start = time.time()
try:
    result = subprocess.run(
        ["drutil", "-drive", "1", "tray", "eject"],
        timeout=5.0,
        capture_output=True,
        text=True
    )
    elapsed = time.time() - start
    print(f"   Completed in {elapsed:.1f}s")
    print(f"   Return code: {result.returncode}")
    if result.stderr:
        print(f"   Stderr: {result.stderr}")
except subprocess.TimeoutExpired:
    print(f"   ❌ Timeout after 5 seconds!")
except Exception as e:
    print(f"   ❌ Error: {e}")