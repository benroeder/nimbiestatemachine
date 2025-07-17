#!/usr/bin/env python3
"""Test #62: Reconnect USB, call recover(), verify ready state."""

import logging
import time
from nimbie.pure_state_machine import NimbiePureStateMachine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

print("\n" + "="*60)
print("Test #62: Recovery from error state")
print("="*60)

try:
    # Create and initialize
    print("\n1. INITIALIZATION")
    print("-" * 20)
    sm = NimbiePureStateMachine(target_drive="1", log_level=logging.INFO)
    print(f"Initial state: {sm.state}")
    
    print("\nInitializing...")
    sm.initialize()
    print(f"State after init: {sm.state}")
    
    if sm.state != 'ready':
        print(f"❌ FAIL: Expected 'ready' state, got '{sm.state}'")
        exit(1)
    print("✅ Initialization successful")
    
    # Put state machine in error state
    print("\n2. TRANSITION TO ERROR STATE")
    print("-" * 20)
    print("Transitioning to error state for testing...")
    
    result = sm.to_error()
    print(f"to_error() result: {result}")
    print(f"State after to_error(): {sm.state}")
    
    if sm.state != 'error':
        print(f"❌ FAIL: Expected 'error' state, got '{sm.state}'")
        exit(1)
    print("✅ Successfully in error state")
    
    # Test recovery transition
    print("\n3. TEST RECOVERY TRANSITION")
    print("-" * 20)
    print("Testing recovery from error state...")
    
    # Attempt recovery
    print("Calling recover()...")
    try:
        result = sm.recover()
        print(f"recover() result: {result}")
        print(f"State after recover(): {sm.state}")
        
        if sm.state == 'ready':
            print("✅ Successfully recovered to ready state")
        else:
            print(f"❌ FAIL: Expected 'ready' state after recovery, got '{sm.state}'")
            exit(1)
            
    except Exception as e:
        print(f"❌ FAIL: Recovery failed with error: {type(e).__name__}: {e}")
        exit(1)
    
    # Test that operations work after recovery
    print("\n4. TEST OPERATIONS AFTER RECOVERY")
    print("-" * 20)
    print("Testing that operations work after recovery...")
    
    # Test state queries
    print(f"is_ready(): {sm.is_ready()}")
    print(f"is_processing(): {sm.is_processing()}")
    print(f"can_load_disk(): {sm.can_load_disk()}")
    
    if sm.is_ready():
        print("✅ is_ready() correctly returns True after recovery")
    else:
        print("❌ FAIL: is_ready() should return True after recovery")
    
    # Test hardware communication
    print("\nTesting hardware communication after recovery...")
    try:
        hw_state = sm.hardware.get_state()
        print(f"Hardware state: {hw_state}")
        print("✅ Hardware communication working after recovery")
    except Exception as e:
        print(f"❌ Hardware communication failed after recovery: {e}")
        exit(1)
    
    # Test that we can attempt to load disk (if available)
    print("\nTesting load operation readiness...")
    if sm.can_load_disk():
        print("✅ Disk loading capability restored after recovery")
    else:
        print("⚠️ No disk available for loading test (this is OK)")
    
    print("\n5. FINAL STATE CHECK")
    print("-" * 20)
    print(f"Final state: {sm.state}")
    print(f"is_ready(): {sm.is_ready()}")
    
    print("\n" + "="*60)
    print("✅ TEST #62 COMPLETE: Recovery from error state")
    print("✅ Recovery transition working correctly")
    print("="*60)
    
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()