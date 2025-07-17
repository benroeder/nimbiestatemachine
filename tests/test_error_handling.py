#!/usr/bin/env python3
"""Test #60: Error handling - test error state transition."""

import logging
import time
from nimbie.pure_state_machine import NimbiePureStateMachine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

print("\n" + "="*60)
print("Test #60: Error handling - test error state transition")
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
    
    # Test manual error state transition
    print("\n2. TEST ERROR STATE TRANSITION")
    print("-" * 20)
    print("Testing manual error state transition...")
    
    # Check current state
    print(f"Current state: {sm.state}")
    
    # Manually trigger error state
    print("Triggering error state...")
    result = sm.to_error()
    print(f"to_error() result: {result}")
    print(f"State after to_error(): {sm.state}")
    
    if sm.state == 'error':
        print("✅ Successfully transitioned to error state")
    else:
        print(f"❌ FAIL: Expected 'error' state, got '{sm.state}'")
        exit(1)
    
    # Test that operations are blocked in error state
    print("\n3. TEST OPERATIONS BLOCKED IN ERROR STATE")
    print("-" * 20)
    print("Testing that operations are blocked in error state...")
    
    # Try to load disk - should fail
    print("Attempting load_next_disk() from error state...")
    try:
        result = sm.load_next_disk()
        print(f"load_next_disk() result: {result}")
        if result:
            print("❌ FAIL: load_next_disk() should not succeed from error state")
            exit(1)
        else:
            print("✅ load_next_disk() correctly failed from error state")
    except Exception as e:
        print(f"✅ load_next_disk() correctly blocked: {type(e).__name__}: {e}")
    
    # Test state queries in error state
    print("\n4. TEST STATE QUERIES IN ERROR STATE")
    print("-" * 20)
    print("Testing state queries in error state...")
    
    print(f"is_ready(): {sm.is_ready()}")
    print(f"is_processing(): {sm.is_processing()}")
    print(f"can_load_disk(): {sm.can_load_disk()}")
    
    if not sm.is_ready():
        print("✅ is_ready() correctly returns False in error state")
    else:
        print("❌ FAIL: is_ready() should return False in error state")
    
    print("\n5. FINAL STATE CHECK")
    print("-" * 20)
    print(f"Final state: {sm.state}")
    
    print("\n" + "="*60)
    print("✅ TEST #60 COMPLETE: Error state handling")
    print("✅ Error state transition working correctly")
    print("="*60)
    
    print("\nNOTE: Error state transition works. For USB disconnect test,")
    print("please manually disconnect USB cable and observe hardware errors.")
    
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()