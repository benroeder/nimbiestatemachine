#!/usr/bin/env python3
"""Test is_processing() method."""

import logging
from nimbie.pure_state_machine import NimbiePureStateMachine

logging.basicConfig(level=logging.WARNING)

print("\nTest #45: is_processing() returns True with disk loaded")
print("=" * 50)

try:
    # Create and initialize
    print("1. Creating state machine...")
    sm = NimbiePureStateMachine(target_drive="1", log_level=logging.WARNING)
    
    # Test in initial state
    print(f"\n2. Initial state: {sm.state}")
    print(f"   is_processing(): {sm.is_processing()}")
    if sm.is_processing():
        print("   ❌ FAIL: Should be False in initial state")
    else:
        print("   ✅ Correct: False in initial state")
    
    # Initialize
    sm.initialize()
    print(f"\n3. After init state: {sm.state}")
    print(f"   is_processing(): {sm.is_processing()}")
    if sm.is_processing():
        print("   ❌ FAIL: Should be False in ready state")
    else:
        print("   ✅ Correct: False in ready state")
    
    # Check if we can load a disk
    hw_state = sm.hardware.get_state()
    if not hw_state['disk_available']:
        print("\n⚠️ No disk available. Testing method works but can't test with disk loaded.")
        print("✅ Method works correctly for non-processing states")
        exit(0)
    
    # Load disk
    print("\n4. Loading disk...")
    sm.load_disk()
    
    # Test in processing state
    print(f"\n5. After loading state: {sm.state}")
    print(f"   is_processing(): {sm.is_processing()}")
    if sm.state == 'processing' and sm.is_processing():
        print("   ✅ SUCCESS: is_processing() returns True in processing state")
    elif sm.state == 'processing' and not sm.is_processing():
        print("   ❌ FAIL: is_processing() returns False in processing state")
    else:
        print(f"   ⚠️ Not in processing state, current state: {sm.state}")
        
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()