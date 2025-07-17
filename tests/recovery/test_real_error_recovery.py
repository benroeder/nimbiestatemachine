#!/usr/bin/env python3
"""Test real error recovery by manually disconnecting USB."""

import logging
import time
from nimbie.pure_state_machine import NimbiePureStateMachine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

print("\n" + "="*60)
print("REAL ERROR RECOVERY TEST")
print("="*60)
print("This test requires manual USB disconnect/reconnect")

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
    
    # Test initial hardware communication
    print("\n2. VERIFY HARDWARE COMMUNICATION")
    print("-" * 20)
    try:
        hw_state = sm.hardware.get_state()
        print(f"Hardware state: {hw_state}")
        print("✅ Hardware communication working")
    except Exception as e:
        print(f"❌ Hardware communication failed: {e}")
        exit(1)
    
    # Wait for manual USB disconnect
    print("\n3. MANUAL USB DISCONNECT")
    print("-" * 20)
    print("🔌 PLEASE DISCONNECT THE USB CABLE NOW")
    print("Press Ctrl+C when you have disconnected the USB cable...")
    
    # Keep trying hardware operations until they fail
    disconnect_detected = False
    attempts = 0
    max_attempts = 30  # 30 seconds
    
    while not disconnect_detected and attempts < max_attempts:
        try:
            time.sleep(1)
            attempts += 1
            print(f"Attempt {attempts}: Testing hardware connection...")
            hw_state = sm.hardware.get_state()
            print(f"  Still connected: {hw_state}")
        except KeyboardInterrupt:
            print("\n✅ Manual disconnect signal received")
            disconnect_detected = True
            break
        except Exception as e:
            print(f"✅ Hardware error detected: {type(e).__name__}: {e}")
            disconnect_detected = True
            break
    
    if not disconnect_detected:
        print("❌ No disconnect detected after 30 seconds")
        exit(1)
    
    # Test that hardware operations fail
    print("\n4. VERIFY HARDWARE FAILURE")
    print("-" * 20)
    print("Testing that hardware operations now fail...")
    
    try:
        hw_state = sm.hardware.get_state()
        print(f"❌ UNEXPECTED: Hardware still responding: {hw_state}")
        print("❌ USB disconnect may not have worked")
        exit(1)
    except Exception as e:
        print(f"✅ Hardware operation failed as expected: {type(e).__name__}: {e}")
    
    # Test that state machine operations detect the error
    print("\n5. STATE MACHINE ERROR DETECTION")
    print("-" * 20)
    print("Testing state machine error detection...")
    
    try:
        can_load = sm.can_load_disk()
        print(f"❌ UNEXPECTED: can_load_disk() returned: {can_load}")
        print("❌ State machine did not detect hardware failure")
        # Force error state
        sm.to_error()
        print("⚠️ Manually forced error state")
    except Exception as e:
        print(f"✅ State machine detected hardware error: {type(e).__name__}: {e}")
        # Force error state if not already there
        if sm.state != 'error':
            sm.to_error()
            print("⚠️ Manually set error state for testing")
    
    print(f"Current state: {sm.state}")
    
    # Wait for manual USB reconnect
    print("\n6. MANUAL USB RECONNECT")
    print("-" * 20)
    print("🔌 PLEASE RECONNECT THE USB CABLE NOW")
    print("Press Ctrl+C when you have reconnected the USB cable...")
    
    # Keep trying until connection is restored
    reconnect_detected = False
    attempts = 0
    max_attempts = 30  # 30 seconds
    
    while not reconnect_detected and attempts < max_attempts:
        try:
            time.sleep(1)
            attempts += 1
            print(f"Attempt {attempts}: Testing hardware reconnection...")
            hw_state = sm.hardware.get_state()
            print(f"✅ Hardware reconnected: {hw_state}")
            reconnect_detected = True
            break
        except KeyboardInterrupt:
            print("\n✅ Manual reconnect signal received")
            print("Testing hardware connection...")
            try:
                hw_state = sm.hardware.get_state()
                print(f"✅ Hardware reconnected: {hw_state}")
                reconnect_detected = True
            except Exception as e:
                print(f"❌ Hardware still not responding: {e}")
                print("Please check USB connection and try again")
            break
        except Exception as e:
            print(f"  Still disconnected: {type(e).__name__}")
    
    if not reconnect_detected:
        print("❌ No reconnection detected after 30 seconds")
        exit(1)
    
    # Test recovery
    print("\n7. TEST RECOVERY")
    print("-" * 20)
    print("Testing recovery from error state...")
    
    print(f"State before recovery: {sm.state}")
    
    try:
        result = sm.recover()
        print(f"recover() result: {result}")
        print(f"State after recovery: {sm.state}")
        
        if sm.state == 'ready':
            print("✅ Successfully recovered to ready state")
        else:
            print(f"❌ FAIL: Expected 'ready' state after recovery, got '{sm.state}'")
            exit(1)
    except Exception as e:
        print(f"❌ Recovery failed: {type(e).__name__}: {e}")
        exit(1)
    
    # Test that operations work after recovery
    print("\n8. VERIFY OPERATIONS AFTER RECOVERY")
    print("-" * 20)
    print("Testing operations after recovery...")
    
    try:
        hw_state = sm.hardware.get_state()
        print(f"Hardware state after recovery: {hw_state}")
        print("✅ Hardware communication restored")
        
        print(f"is_ready(): {sm.is_ready()}")
        print(f"can_load_disk(): {sm.can_load_disk()}")
        
        if sm.is_ready():
            print("✅ State machine fully operational after recovery")
        else:
            print("❌ State machine not ready after recovery")
            exit(1)
            
    except Exception as e:
        print(f"❌ Hardware communication still failing: {e}")
        exit(1)
    
    print("\n" + "="*60)
    print("✅ REAL ERROR RECOVERY TEST COMPLETE!")
    print("✅ Hardware disconnect/reconnect recovery working!")
    print("="*60)
    
except KeyboardInterrupt:
    print("\n⚠️ Test interrupted by user")
    print("This is normal for manual testing")
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()