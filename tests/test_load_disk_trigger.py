#!/usr/bin/env python3
"""Test load_disk trigger with and without disk available."""

import logging
from nimbie.pure_state_machine import NimbiePureStateMachine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

print("Test #18 & #19: Load Disk Trigger Test")
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
    
    if not disk_available:
        print("\nTest #18: Testing load_disk with NO disk available")
        print("Attempting to trigger load_disk...")
        result = sm.load_disk()
        print(f"Trigger result: {result}")
        print(f"State after trigger: {sm.state}")
        if sm.state == 'ready':
            print("✅ SUCCESS: Trigger failed gracefully, state remained 'ready'")
        else:
            print(f"❌ FAIL: Expected state 'ready', got '{sm.state}'")
    else:
        print("\nTest #19: Testing load_disk WITH disk available")
        print("Attempting to trigger load_disk...")
        result = sm.load_disk()
        print(f"Trigger result: {result}")
        print(f"State after trigger: {sm.state}")
        if sm.state == 'loading':
            print("✅ SUCCESS: Transition to 'loading' state successful")
        else:
            print(f"❌ FAIL: Expected state 'loading', got '{sm.state}'")
    
    # Try from wrong state
    print("\nTesting load_disk from wrong state...")
    if sm.state != 'ready':
        # Reset to ready first
        sm.machine.set_state('ready')
    sm.machine.set_state('processing')  # Force to wrong state
    print(f"Current state: {sm.state}")
    result = sm.load_disk()
    print(f"Trigger from wrong state result: {result}")
    if not result:
        print("✅ SUCCESS: Trigger correctly rejected from wrong state")
    else:
        print("❌ FAIL: Trigger should not work from processing state")
        
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()