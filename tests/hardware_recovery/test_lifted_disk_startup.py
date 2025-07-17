#!/usr/bin/env python3
"""Test startup with a disk already lifted by the dropper."""

import logging
from nimbie import NimbieStateMachine

print("Test: Startup with disk already lifted")
print("=" * 50)

# First, create a scenario with a lifted disk
print("\nStep 1: Setting up a lifted disk scenario...")
sm1 = NimbieStateMachine(target_drive="1", log_level=logging.WARNING)

with sm1.manual_operation():
    state = sm1.get_hardware_state()
    
    # If no disk is available, we can't test this
    if not state['disk_available']:
        print("No disks available for testing")
        exit(1)
    
    # Open tray if needed
    if not state['tray_out']:
        sm1.manual_open_tray()
    
    # Place disk
    print("  Placing disk on tray...")
    sm1.manual_place_disk()
    
    # Lift disk
    print("  Lifting disk...")
    sm1.manual_lift_disk()
    
    print("  Disk is now lifted by the dropper")
    
    state = sm1.get_hardware_state()
    print(f"  Disk lifted: {state['disk_lifted']}")

# Delete first instance
del sm1

print("\n" + "=" * 50)
print("Step 2: Creating new state machine to test improved startup")
print("The startup should detect and clear the lifted disk\n")

# Create new instance with INFO logging to see the startup procedure
sm2 = NimbieStateMachine(target_drive="1", log_level=logging.INFO)

print("\nChecking final state...")
state = sm2.get_hardware_state()
print(f"  Disk lifted: {state['disk_lifted']}")
print(f"  Tray out: {state['tray_out']}")
print(f"  State machine: {sm2.state}")

print("\nTest complete!")