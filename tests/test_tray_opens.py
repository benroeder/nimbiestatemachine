#!/usr/bin/env python3
"""Test that tray physically opens when load_disk is triggered."""

import logging
import time
from nimbie.pure_state_machine import NimbiePureStateMachine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

print("\nTest #21: Verify tray physically opens")
print("=" * 50)
print("WATCH THE HARDWARE - tray should open when load_disk is triggered")
print()

try:
    # Create and initialize state machine
    print("Creating and initializing state machine...")
    sm = NimbiePureStateMachine(target_drive="1", log_level=logging.INFO)
    sm.initialize()
    print(f"Current state: {sm.state}")
    
    # Check if disk is available
    hw_state = sm.hardware.get_state()
    disk_available = hw_state['disk_available']
    print(f"\nDisk available in queue: {disk_available}")
    
    if disk_available:
        print("\n🎯 Triggering load_disk - WATCH FOR TRAY OPENING...")
        result = sm.load_disk()
        print(f"Trigger result: {result}")
        print(f"State after trigger: {sm.state}")
        
        # Give time to observe the tray
        print("\nWaiting 3 seconds to observe tray...")
        time.sleep(3)
        
        # Check hardware state
        hw_state = sm.hardware.get_state()
        tray_out = hw_state.get('tray_out', False)
        print(f"\nHardware reports tray_out: {tray_out}")
        
        if tray_out:
            print("✅ SUCCESS: Tray physically opened!")
        else:
            print("❌ FAIL: Tray did not open or sensor not detecting")
            print("Note: Check if tray actually opened visually")
    else:
        print("No disk available. Cannot test tray opening.")
        print("Please add a disk to the queue and run this test again.")
        
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()