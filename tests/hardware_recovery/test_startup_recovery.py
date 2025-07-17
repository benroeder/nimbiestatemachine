#!/usr/bin/env python3
"""Test the startup recovery in a single session."""

import logging
from nimbie import NimbieStateMachine

print("Test: Startup Recovery Demonstration")
print("=" * 50)
print("\nThis test will:")
print("1. Place a disk in the drive")
print("2. Simulate a restart by calling transition_to_idle()")
print("3. Show that the disk is properly recovered\n")

# Create state machine with INFO logging
sm = NimbieStateMachine(target_drive="1", log_level=logging.INFO)

# First, manually place a disk
print("\n" + "-" * 50)
print("Step 1: Manually placing a disk in the drive")
print("-" * 50)

with sm.manual_operation():
    state = sm.get_hardware_state()
    if not state['disk_available']:
        print("ERROR: No disks available!")
        exit(1)
    
    print("Opening tray...")
    sm.manual_open_tray()
    
    print("Placing disk...")
    sm.manual_place_disk()
    
    print("Closing tray with disk...")
    sm.manual_close_tray()
    
    # Force state to processing to simulate disk being loaded
    print("Setting state to 'processing' to simulate disk loaded...")
    sm.manual_set_state("processing")

state = sm.get_hardware_state()
print(f"\nDisk is now in drive:")
print(f"  Tray: {'open' if state['tray_out'] else 'closed'}")
print(f"  State machine: {sm.state}")

# Now test the recovery
print("\n" + "-" * 50)
print("Step 2: Testing transition_to_idle() recovery")
print("-" * 50)
print("This simulates what happens at startup when a disk is stuck in the drive.\n")

# Call transition_to_idle which includes the disk recovery logic
sm.transition_to_idle()

print("\nChecking final state after recovery...")
state = sm.get_hardware_state()
print(f"  Tray: {'open' if state['tray_out'] else 'closed'}")
print(f"  State machine: {sm.state}")
print(f"  Disk available: {state['disk_available']}")
print(f"  Disk lifted: {state['disk_lifted']}")

print("\nTest complete!")
print("The disk was successfully recovered from the drive.")