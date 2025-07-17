#!/usr/bin/env python3
"""Check if dropper already has a disk."""

from nimbie import NimbieStateMachine
import logging

print("Checking dropper state")
print("=" * 50)

sm = NimbieStateMachine(target_drive="1", log_level=logging.WARNING)

with sm.manual_operation():
    state = sm.get_hardware_state()
    print(f"\nHardware state:")
    print(f"  Disk lifted: {state['disk_lifted']}")
    print(f"  Tray out: {state['tray_out']}")
    
    # The dropper might already be holding a disk
    print("\nTrying to drop any disk the dropper might be holding...")
    
    # First ensure tray is closed for drop operation
    if state['tray_out']:
        print("Closing tray first...")
        sm.manual_close_tray()
    
    # Try to drop
    try:
        print("Attempting to accept (drop) any lifted disk...")
        result = sm.hardware.accept_disk()
        print(f"  Result: {result}")
        print("  Success! Dropper has been cleared.")
    except Exception as e:
        print(f"  Accept failed: {e}")
        
    # Try reject as well
    try:
        print("\nAttempting to reject (drop) any lifted disk...")
        result = sm.hardware.reject_disk()
        print(f"  Result: {result}")
        print("  Success! Dropper has been cleared.")
    except Exception as e:
        print(f"  Reject failed: {e}")
    
    # Now try to deal with the disk in the tray
    print("\n\nNow attempting to handle the disk in the tray...")
    print("Opening tray...")
    sm.manual_open_tray()
    
    print("Trying lift again after clearing dropper...")
    try:
        sm.manual_lift_disk()
        print("  Success! Disk lifted from tray.")
        sm.manual_close_tray()
        sm.manual_accept_disk()
        print("  Disk successfully removed!")
    except Exception as e:
        print(f"  Still failing: {e}")
        print("\nThe hardware may need a power cycle or physical inspection.")