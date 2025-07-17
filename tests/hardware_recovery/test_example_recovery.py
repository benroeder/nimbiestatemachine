#!/usr/bin/env python3
"""Test if the example properly recovers from a disk in drive."""

from nimbie import NimbieStateMachine
import logging

print("Testing example_state_machine.py behavior with disk in drive")
print("=" * 60)

# First, let's set up a disk in the drive
print("\nStep 1: Setting up disk in drive...")
sm1 = NimbieStateMachine(target_drive="1", log_level=logging.WARNING)
with sm1.manual_operation():
    state = sm1.get_hardware_state()
    if state['disk_available']:
        sm1.manual_open_tray()
        sm1.manual_place_disk()
        sm1.manual_close_tray()
        print("Disk placed in drive.")
    else:
        print("No disk available to test with.")
        exit(1)

# Delete the first instance
del sm1

print("\n" + "=" * 60)
print("Step 2: Running example initialization (like example_state_machine.py)...")
print("This should show the startup disk check recovering the disk:\n")

# Now create a new instance like the example does
try:
    sm = NimbieStateMachine(target_drive="1")  # Default INFO logging
    print("\nState machine initialized successfully!")
    
    # Check state like the example does
    hw_state = sm.get_hardware_state()
    print(f"\nHardware state after initialization:")
    print(f"  Disks available: {'Yes' if hw_state['disk_available'] else 'No'}")
    print(f"  Tray status: {'Open' if hw_state['tray_out'] else 'Closed'}")
    print(f"  Current state: {sm.state}")
    
except Exception as e:
    print(f"Failed to initialize: {e}")