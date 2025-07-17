#!/usr/bin/env python3
"""Force disk removal when hardware state is inconsistent."""

from nimbie import NimbieStateMachine
import logging

print("Force disk removal - assuming disk IS present")
print("=" * 50)

sm = NimbieStateMachine(target_drive="1", log_level=logging.WARNING)

with sm.manual_operation():
    print("\nCurrent hardware reports:")
    state = sm.get_hardware_state()
    print(f"  Tray out: {state['tray_out']}")
    print(f"  Disk in tray: {state['disk_in_open_tray']}")
    print(f"  Disk lifted: {state['disk_lifted']}")
    
    print("\nBUT we know there IS a disk in the tray.")
    print("Attempting forced removal sequence...\n")
    
    # If tray is open, close it first
    if state['tray_out']:
        print("Step 1: Closing tray with disk...")
        sm.manual_close_tray()
    
    # Now open it again
    print("Step 2: Opening tray...")
    sm.manual_open_tray()
    
    # Force lift attempt regardless of state
    print("Step 3: Forcing lift command (ignoring state)...")
    try:
        # Direct hardware command
        result = sm.hardware.lift_disk()
        print(f"  Lift result: {result}")
        
        # If we got here, it worked
        print("Step 4: Closing tray...")
        sm.manual_close_tray()
        
        print("Step 5: Dropping disk...")
        sm.manual_accept_disk()
        
        print("\nSuccess! Disk has been removed.")
        
    except Exception as e:
        print(f"  Error: {e}")
        
        # Try alternate approach
        print("\nTrying alternate approach...")
        print("Please manually remove the disk from the tray.")
        input("Press Enter when disk has been removed...")
        
        # Close tray
        print("Closing empty tray...")
        sm.manual_close_tray()
        
    # Final state check
    print("\nFinal state:")
    state = sm.get_hardware_state()
    print(f"  Tray out: {state['tray_out']}")
    print(f"  Disk in tray: {state['disk_in_open_tray']}")
    print(f"  Disk lifted: {state['disk_lifted']}")