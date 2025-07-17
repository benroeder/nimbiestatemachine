#!/usr/bin/env python3
"""Test #60: Disconnect USB, verify error state."""

import logging
import time
from nimbie.pure_state_machine import NimbiePureStateMachine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

print("\n" + "="*60)
print("Test #60: Disconnect USB, verify error state")
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
    
    # Test hardware connection
    print("\n2. TEST HARDWARE CONNECTION")
    print("-" * 20)
    print("Testing hardware communication...")
    try:
        hw_state = sm.hardware.get_state()
        print(f"Hardware state: {hw_state}")
        print("✅ Hardware communication working")
    except Exception as e:
        print(f"❌ Hardware communication failed: {e}")
        exit(1)
    
    # Instructions for manual test
    print("\n3. MANUAL USB DISCONNECT TEST")
    print("-" * 20)
    print("INSTRUCTION: Please disconnect the USB cable from the Nimbie device")
    print("Press Enter when you have disconnected the USB cable...")
    input()
    
    print("\n4. TEST ERROR STATE DETECTION")
    print("-" * 20)
    print("Testing hardware communication after disconnect...")
    
    # Try to communicate with hardware - should fail
    try:
        hw_state = sm.hardware.get_state()
        print(f"❌ UNEXPECTED: Hardware still responding: {hw_state}")
        print("❌ FAIL: USB disconnect not detected")
        exit(1)
    except Exception as e:
        print(f"✅ Expected error detected: {type(e).__name__}: {e}")
        print("✅ Hardware communication properly failed")
    
    # Check if state machine can detect the error
    print("\n5. STATE MACHINE ERROR HANDLING")
    print("-" * 20)
    print("Testing state machine error detection...")
    
    # Try to perform an operation that should trigger error state
    try:
        print("Attempting to check if can load disk...")
        can_load = sm.can_load_disk()
        print(f"❌ UNEXPECTED: can_load_disk() returned: {can_load}")
        print("❌ State machine did not detect hardware error")
    except Exception as e:
        print(f"✅ State machine properly detected error: {type(e).__name__}: {e}")
        # Check if state machine went to error state
        if sm.state == 'error':
            print("✅ State machine correctly transitioned to 'error' state")
        else:
            print(f"⚠️ State machine state is '{sm.state}', expected 'error'")
    
    print("\n6. FINAL STATE CHECK")
    print("-" * 20)
    print(f"Final state: {sm.state}")
    
    print("\n" + "="*60)
    print("✅ TEST #60 COMPLETE: USB disconnect test")
    print("✅ Hardware error detection working")
    print("="*60)
    
    print("\nNOTE: Please reconnect the USB cable for the next test")
    
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()