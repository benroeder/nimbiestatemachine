#!/usr/bin/env python3
"""Reset hardware to clean state."""

from nimbie import NimbieDriver
import time

print("Resetting hardware to clean state...")
d = NimbieDriver('1')

# Get current state
state = d.get_state()
print(f"Current: tray_out={state['tray_out']}, disk_lifted={state['disk_lifted']}")

# If tray is open, close it
if state['tray_out']:
    print("Closing tray...")
    try:
        d.close_tray()
        time.sleep(2)
    except:
        pass

# If disk is lifted, drop it
if state['disk_lifted']:
    print("Dropping lifted disk...")
    try:
        d.reject_disk()
    except:
        pass

print("Hardware reset complete")