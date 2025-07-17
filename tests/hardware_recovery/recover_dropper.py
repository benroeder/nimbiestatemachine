#!/usr/bin/env python3
"""Recover the dropper from error state."""

import logging
from nimbie import NimbieStateMachine

print("Attempting to recover dropper from error state...")
print("=" * 50)

sm = NimbieStateMachine(target_drive="1", log_level=logging.WARNING)

with sm.manual_operation():
    print("\nChecking current state...")
    state = sm.get_hardware_state()
    print(f"  Disk available: {state['disk_available']}")
    print(f"  Tray out: {state['tray_out']}")
    print(f"  Disk lifted: {state['disk_lifted']}")
    
    # Try to recover by attempting various operations
    print("\nAttempting recovery operations...")
    
    # Ensure tray is closed first
    if state['tray_out']:
        print("Closing tray...")
        sm.manual_close_tray()
    
    # Try to drop any lifted disk
    try:
        print("Attempting to accept any lifted disk...")
        sm.manual_accept_disk()
        print("  Success - disk dropped")
    except Exception as e:
        print(f"  No lifted disk or error: {e}")
    
    # Try reject as well
    try:
        print("Attempting to reject...")
        sm.manual_reject_disk()
        print("  Success - reject operation completed")
    except Exception as e:
        print(f"  Reject failed: {e}")
    
    # Open tray and check state
    print("\nOpening tray to check state...")
    sm.manual_open_tray()
    
    state = sm.get_hardware_state()
    print(f"\nFinal state:")
    print(f"  Disk available: {state['disk_available']}")
    print(f"  Tray out: {state['tray_out']}")
    print(f"  Disk in tray: {state['disk_in_open_tray']}")
    print(f"  Disk lifted: {state['disk_lifted']}")

print("\nRecovery complete. The dropper should now be in a working state.")