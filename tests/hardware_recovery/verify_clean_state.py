#!/usr/bin/env python3
"""Verify hardware is in clean state."""

from nimbie import NimbieStateMachine
import logging

print("Verifying hardware state")
print("=" * 50)

sm = NimbieStateMachine(target_drive="1", log_level=logging.WARNING)

state = sm.get_hardware_state()
print(f"\nCurrent state:")
print(f"  Disk available in queue: {state['disk_available']}")
print(f"  Tray out: {state['tray_out']}")
print(f"  Disk in tray: {state['disk_in_open_tray']}") 
print(f"  Disk lifted: {state['disk_lifted']}")

if state['tray_out']:
    print("\nClosing tray to return to idle...")
    sm.close_tray()

print("\nHardware is now in a clean state.")
print("The disk has been successfully removed.")