#!/usr/bin/env python3
"""Manually remove disk from tray using different approach."""

from nimbie import NimbieStateMachine
import logging

print("Manual disk removal")
print("=" * 40)

sm = NimbieStateMachine(target_drive="1", log_level=logging.WARNING)

with sm.manual_operation():
    state = sm.get_hardware_state()
    print(f"\nInitial state:")
    print(f"  Tray out: {state['tray_out']}")
    print(f"  Disk in tray: {state['disk_in_open_tray']}")
    
    if state['disk_in_open_tray'] and state['tray_out']:
        print("\nDisk detected in open tray.")
        
        # First, try to reset the dropper by closing and opening tray
        print("\nResetting dropper mechanism...")
        print("  Closing tray...")
        sm.manual_close_tray()
        
        print("  Opening tray again...")
        sm.manual_open_tray()
        
        # Now try to lift again
        print("\nAttempting to lift disk after reset...")
        try:
            sm.manual_lift_disk()
            print("  Success! Disk lifted.")
            
            # Close tray and drop
            print("  Closing tray...")
            sm.manual_close_tray()
            
            print("  Accepting disk...")
            sm.manual_accept_disk()
            print("  Disk removed successfully!")
            
        except Exception as e:
            print(f"  Still getting error: {e}")
            print("\nThe dropper mechanism may need physical inspection.")
            print("Please check if:")
            print("  1. The gripper is physically stuck")
            print("  2. There's an obstruction in the mechanism")
            print("  3. The disk is properly seated in the tray")