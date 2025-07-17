#!/usr/bin/env python3
"""Advanced hardware reset to handle dropper errors."""

from nimbie import NimbieDriver
import time

print("Advanced hardware reset...")
d = NimbieDriver('1')

# Get current state
try:
    state = d.get_state()
    print(f"Current: tray_out={state['tray_out']}, disk_lifted={state['disk_lifted']}")
except Exception as e:
    print(f"Error getting state: {e}")

# If disk is lifted, drop it first
try:
    state = d.get_state()
    if state['disk_lifted']:
        print("Dropping lifted disk...")
        if state['tray_out']:
            d.close_tray()
            time.sleep(2)
        d.reject_disk()
        time.sleep(2)
except Exception as e:
    print(f"Error dropping disk: {e}")

# If tray is open, close it
try:
    state = d.get_state()
    if state['tray_out']:
        print("Closing tray...")
        d.close_tray()
        time.sleep(2)
except Exception as e:
    print(f"Error closing tray: {e}")

# Try to clear any dropper error by attempting a reject operation
# This might reset the dropper state
print("Attempting to clear dropper state...")
try:
    # Try to reject (this might clear the dropper error)
    d.reject_disk()
    time.sleep(1)
    print("Dropper reset attempt completed")
except Exception as e:
    print(f"Dropper reset error (this might be expected): {e}")

# Final state check
try:
    state = d.get_state()
    print(f"Final state: tray_out={state['tray_out']}, disk_lifted={state['disk_lifted']}")
    print("Advanced hardware reset complete")
except Exception as e:
    print(f"Error getting final state: {e}")