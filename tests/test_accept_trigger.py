#!/usr/bin/env python3
"""Test accept_disk trigger changes state."""

import logging
from nimbie.pure_state_machine import NimbiePureStateMachine

logging.basicConfig(level=logging.WARNING)

print("\nTest #47: Trigger accept_disk, verify state change")
print("=" * 50)

try:
    # Create and initialize
    print("1. Creating state machine...")
    sm = NimbiePureStateMachine(target_drive="1", log_level=logging.WARNING)
    sm.initialize()
    
    # Manually set to processing state for testing
    print("\n2. Setting state to processing...")
    sm.machine.set_state('processing')
    print(f"   Current state: {sm.state}")
    
    # Test accept_disk trigger
    print("\n3. Triggering accept_disk...")
    result = sm.accept_disk()
    print(f"   Trigger result: {result}")
    print(f"   New state: {sm.state}")
    
    # Check if we're in unloading state
    if sm.state.startswith('unloading'):
        print("   ✅ SUCCESS: Transitioned to unloading state")
        
        # Check specific sub-state
        if sm.state == 'unloading_opening_tray':
            print("   ✅ Correct sub-state: unloading_opening_tray")
        else:
            print(f"   ⚠️ Unexpected sub-state: {sm.state}")
    else:
        print(f"   ❌ FAIL: Expected unloading state, got {sm.state}")
    
    # Test from wrong state
    print("\n4. Testing from wrong state...")
    sm.machine.set_state('ready')
    result = sm.accept_disk()
    if not result:
        print("   ✅ Correctly rejected from ready state")
    else:
        print("   ❌ Should not accept from ready state")
        
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()