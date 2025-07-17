#!/usr/bin/env python3
"""Test that polling automatically transitions when tray opens."""

import logging
import time
from nimbie.pure_state_machine import NimbiePureStateMachine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

print("\nTest #33: Verify auto-transition when tray opens")
print("=" * 50)
print("WATCH: Should automatically transition to placing_disk when tray opens")
print()

try:
    # Create and initialize state machine
    print("Creating and initializing state machine...")
    sm = NimbiePureStateMachine(target_drive="1", log_level=logging.INFO)
    sm.initialize()
    
    # Check if disk is available
    hw_state = sm.hardware.get_state()
    if not hw_state['disk_available']:
        print("No disk available. Cannot test.")
        exit(1)
    
    # Start loading process
    print("\nStarting load_disk - tray should open...")
    sm.load_disk()
    print(f"Initial state: {sm.state}")
    
    # Wait for automatic transitions
    print("\nWaiting for automatic transitions...")
    max_wait = 15  # seconds
    start_time = time.time()
    last_state = sm.state
    
    while time.time() - start_time < max_wait:
        current_state = sm.state
        if current_state != last_state:
            print(f"State changed: {last_state} → {current_state}")
            last_state = current_state
            
        if current_state == 'loading_placing_disk':
            print("\n✅ SUCCESS: Auto-transitioned to placing_disk when tray opened!")
            break
            
        if current_state == 'error':
            print("\n❌ FAIL: Entered error state")
            break
            
        time.sleep(0.1)
    else:
        print(f"\n❌ Timeout after {max_wait} seconds")
        print(f"Final state: {sm.state}")
    
    # Check hardware state
    hw_state = sm.hardware.get_state()
    print(f"\nHardware state:")
    print(f"  tray_out: {hw_state.get('tray_out')}")
    print(f"  disk_available: {hw_state.get('disk_available')}")
    
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()