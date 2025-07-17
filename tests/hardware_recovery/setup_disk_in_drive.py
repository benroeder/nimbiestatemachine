#!/usr/bin/env python3
"""Setup script to place a disk in the drive for testing startup recovery.

This script places a disk in the drive and then exits. This simulates a 
scenario where the system crashed or lost power with a disk loaded.

To test the recovery, run this script first, then run any script that
creates a new NimbieStateMachine instance to see the startup recovery in action.
"""

import logging
from nimbie import NimbieStateMachine

print("Setup: Place disk in drive for startup recovery testing")
print("=" * 50)

# Create a state machine to manually place a disk
print("\nInitializing state machine...")
sm = NimbieStateMachine(target_drive="1", log_level=logging.WARNING)

with sm.manual_operation():
    # Check if disk is available
    state = sm.get_hardware_state()
    if not state['disk_available']:
        print("ERROR: No disks available in the queue!")
        print("Please add disks to the input queue and try again.")
        exit(1)
    
    print("\nPlacing disk in drive...")
    print("  Opening tray...")
    sm.manual_open_tray()
    
    print("  Placing disk on tray...")
    sm.manual_place_disk()
    
    print("  Closing tray with disk inside...")
    sm.manual_close_tray()
    
    print("\nDisk is now loaded in the drive.")

# Check final state
state = sm.get_hardware_state()
print(f"\nFinal drive state:")
print(f"  Tray: {'open' if state['tray_out'] else 'closed'}")
print(f"  Disk in drive: {not state['tray_out'] and not state['disk_in_open_tray']}")

print("\n" + "=" * 50)
print("Setup complete!")
print("\nTo test the startup recovery:")
print("1. Exit this script (it will happen automatically)")
print("2. Run any script that creates a new NimbieStateMachine")
print("3. Watch the startup procedure detect and remove the disk")
print("\nExample:")
print("  python -c \"from nimbie import NimbieStateMachine; sm = NimbieStateMachine('1')\"")