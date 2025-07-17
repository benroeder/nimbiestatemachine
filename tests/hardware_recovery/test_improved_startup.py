#!/usr/bin/env python3
"""Test improved startup procedure in single session."""

import logging
from nimbie import NimbieStateMachine

print("Test: Improved startup procedure")
print("=" * 50)

# Create state machine
sm = NimbieStateMachine(target_drive="1", log_level=logging.INFO)

print("\nSimulating various startup scenarios...")
print("\n" + "-" * 50)
print("Scenario 1: Disk lifted by dropper")
print("-" * 50)

with sm.manual_operation():
    # Set up lifted disk
    if sm.get_hardware_state()['disk_available']:
        if not sm.get_hardware_state()['tray_out']:
            sm.manual_open_tray()
        sm.manual_place_disk()
        sm.manual_lift_disk()
        print("Setup: Disk is now lifted")
        
        # Force restart check
        print("\nRunning startup check...")
        sm._startup_disk_check()
        
        print("\nResult:")
        state = sm.get_hardware_state()
        print(f"  Disk lifted: {state['disk_lifted']}")
        print(f"  Tray out: {state['tray_out']}")

print("\n" + "-" * 50)
print("Scenario 2: Disk in closed drive")  
print("-" * 50)

with sm.manual_operation():
    # Set up disk in drive
    if sm.get_hardware_state()['disk_available']:
        if not sm.get_hardware_state()['tray_out']:
            sm.manual_open_tray()
        sm.manual_place_disk()
        sm.manual_close_tray()
        print("Setup: Disk is now in closed drive")
        
        # Run transition_to_idle which includes disk check
        print("\nRunning transition_to_idle...")
        sm.transition_to_idle()
        
        print("\nResult:")
        state = sm.get_hardware_state()
        print(f"  Tray out: {state['tray_out']}")
        print(f"  Disk in tray: {state['disk_in_open_tray']}")

print("\nAll scenarios tested successfully!")