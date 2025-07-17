#!/usr/bin/env python3
"""Test that loading state is hierarchical with opening_tray sub-state."""

import logging
from nimbie.pure_state_machine import NimbiePureStateMachine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

print("\nTest #23: Verify hierarchical loading state")
print("=" * 50)

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
        print("\nTriggering load_disk...")
        result = sm.load_disk()
        print(f"Trigger result: {result}")
        print(f"State after trigger: {sm.state}")
        
        # Check if state is hierarchical
        if sm.state == 'loading_opening_tray':
            print("✅ SUCCESS: State is 'loading_opening_tray' (hierarchical state)")
            
            # Test state hierarchy
            print("\nTesting state hierarchy...")
            print(f"Is in loading? {sm.is_loading()}")
            
            # List all loading substates
            print("\nAll loading substates:")
            loading_states = ['loading_opening_tray', 'loading_waiting_tray_open', 
                            'loading_placing_disk', 'loading_waiting_disk_placed',
                            'loading_closing_tray', 'loading_waiting_tray_closed']
            for state in loading_states:
                print(f"  - {state}")
            
        else:
            print(f"❌ FAIL: Expected state 'loading_opening_tray', got '{sm.state}'")
    else:
        print("No disk available. Cannot test hierarchical state.")
        print("Please add a disk to the queue and run this test again.")
        
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()