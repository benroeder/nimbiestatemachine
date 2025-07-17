#!/usr/bin/env python3
"""Check detailed hardware state."""

from nimbie import NimbieStateMachine
import logging

sm = NimbieStateMachine(target_drive="1", log_level=logging.WARNING)

print("\nDetailed hardware state check:")
print("=" * 40)

# Get state
state = sm.get_hardware_state()
print(f"\nParsed state:")
print(f"  Disk available (bit 1): {state['disk_available']}")
print(f"  Disk in open tray (bit 3): {state['disk_in_open_tray']}")  
print(f"  Disk lifted (bit 4): {state['disk_lifted']}")
print(f"  Tray out (bit 5): {state['tray_out']}")

# Try manual operations to diagnose
print("\nManual diagnostic:")
with sm.manual_operation():
    # Open tray to see what's there
    print("Opening tray...")
    sm.manual_open_tray()
    
    state = sm.get_hardware_state()
    print(f"\nWith tray open:")
    print(f"  Disk in tray: {state['disk_in_open_tray']}")
    
    if state['disk_in_open_tray']:
        print("\nDisk found in tray! Lifting it...")
        sm.manual_lift_disk()
        print("Closing tray...")
        sm.manual_close_tray()
        print("Accepting disk...")
        sm.manual_accept_disk()
        print("Disk removed successfully.")
    else:
        print("\nNo disk in tray.")
        sm.manual_close_tray()