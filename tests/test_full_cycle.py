#!/usr/bin/env python3
"""Test full cycle: initialize, load, accept/reject."""

import logging
import time
from nimbie.pure_state_machine import NimbiePureStateMachine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

print("\n" + "="*60)
print("FULL CYCLE TEST - Pure State Machine")
print("="*60)

try:
    # Create and initialize
    print("\n1. INITIALIZATION")
    print("-" * 20)
    sm = NimbiePureStateMachine(target_drive="1", log_level=logging.INFO)
    print(f"Initial state: {sm.state}")
    
    print("\nInitializing (handles any hardware state)...")
    sm.initialize()
    print(f"State after init: {sm.state}")
    
    if sm.state != 'ready':
        print(f"❌ FAIL: Expected 'ready' state, got '{sm.state}'")
        exit(1)
    print("✅ Initialization successful")
    
    # Check if we can load
    print("\n2. PRE-LOAD CHECKS")
    print("-" * 20)
    print(f"is_ready(): {sm.is_ready()}")
    print(f"can_load_disk(): {sm.can_load_disk()}")
    
    hw_state = sm.hardware.get_state()
    print(f"Hardware state:")
    print(f"  disk_available: {hw_state['disk_available']}")
    print(f"  tray_out: {hw_state['tray_out']}")
    
    if not sm.can_load_disk():
        print("\n⚠️ No disk available to load")
        print("Please add a disk to the queue and run again")
        exit(0)
    
    # Load disk
    print("\n3. LOADING DISK")
    print("-" * 20)
    print("Loading next disk...")
    start_time = time.time()
    
    success = sm.load_next_disk()
    load_time = time.time() - start_time
    
    print(f"Load result: {success}")
    print(f"Time taken: {load_time:.1f}s")
    print(f"State after load: {sm.state}")
    print(f"is_processing(): {sm.is_processing()}")
    
    if not success or not sm.is_processing():
        print("❌ FAIL: Load failed")
        exit(1)
    print("✅ Load successful")
    
    # Check hardware state with disk loaded
    print("\n4. PROCESSING STATE")
    print("-" * 20)
    hw_state = sm.hardware.get_state()
    print(f"Hardware with disk loaded:")
    print(f"  disk_available: {hw_state['disk_available']}")
    print(f"  tray_out: {hw_state['tray_out']}")
    print(f"  disk_lifted: {hw_state['disk_lifted']}")
    
    # Accept the disk
    print("\n5. ACCEPTING DISK")
    print("-" * 20)
    print("Accepting current disk...")
    start_time = time.time()
    
    success = sm.accept_current_disk()
    accept_time = time.time() - start_time
    
    print(f"Accept result: {success}")
    print(f"Time taken: {accept_time:.1f}s")
    print(f"State after accept: {sm.state}")
    print(f"is_ready(): {sm.is_ready()}")
    
    if not success or not sm.is_ready():
        print("❌ FAIL: Accept failed")
        exit(1)
    print("✅ Accept successful")
    
    # Try to load another disk
    print("\n6. SECOND DISK CYCLE")
    print("-" * 20)
    
    if sm.can_load_disk():
        print("Loading second disk...")
        success = sm.load_next_disk()
        if success:
            print("✅ Second disk loaded")
            
            # Reject this one
            print("\nRejecting second disk...")
            success = sm.reject_current_disk()
            if success:
                print("✅ Second disk rejected")
            else:
                print("❌ Reject failed")
        else:
            print("❌ Second load failed")
    else:
        print("No second disk available")
    
    # Final state
    print("\n7. FINAL STATE")
    print("-" * 20)
    print(f"Final state: {sm.state}")
    print(f"is_ready(): {sm.is_ready()}")
    
    print("\n" + "="*60)
    print("✅ FULL CYCLE TEST COMPLETE!")
    print("="*60)
    
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()