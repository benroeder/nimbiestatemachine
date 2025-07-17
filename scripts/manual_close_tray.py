#!/usr/bin/env python3
"""Manually close the tray with timeout info."""

import time
from nimbie import NimbieDriver

print("Attempting to close tray...")
d = NimbieDriver('1')

# Check initial state
state = d.get_state()
print(f"Initial state: tray_out={state['tray_out']}")

if not state['tray_out']:
    print("Tray is already closed")
else:
    print("Closing tray (this may take up to 30 seconds)...")
    start = time.time()
    try:
        d.close_tray()
        elapsed = time.time() - start
        print(f"✅ Tray closed successfully in {elapsed:.1f} seconds")
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ Failed after {elapsed:.1f} seconds: {e}")
    
    # Check final state
    state = d.get_state()
    print(f"Final state: tray_out={state['tray_out']}")