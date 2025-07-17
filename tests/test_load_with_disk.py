#!/usr/bin/env python3
"""Test load_disk trigger with disk available."""

import logging
from nimbie.pure_state_machine import NimbiePureStateMachine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

print("\nTest #19: Testing load_disk WITH disk available")
print("=" * 50)

try:
    # Create and initialize state machine
    print("\nCreating and initializing state machine...")
    sm = NimbiePureStateMachine(target_drive="1", log_level=logging.INFO)
    sm.initialize()
    print(f"Current state: {sm.state}")
    
    # Check if disk is available
    hw_state = sm.hardware.get_state()
    disk_available = hw_state['disk_available']
    print(f"\nDisk available in queue: {disk_available}")
    
    if disk_available:
        print("\nAttempting to trigger load_disk...")
        result = sm.load_disk()
        print(f"Trigger result: {result}")
        print(f"State after trigger: {sm.state}")
        if sm.state == 'loading':
            print("✅ SUCCESS: Transition to 'loading' state successful")
        else:
            print(f"❌ FAIL: Expected state 'loading', got '{sm.state}'")
    else:
        print("No disk available. Test skipped.")
        print("Please add a disk to the queue and run this test again.")
        
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()