#!/usr/bin/env python3
"""Test #58: Load disk, then reject - verify drops to reject pile."""

import logging
import time
from nimbie.pure_state_machine import NimbiePureStateMachine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

print("\n" + "="*60)
print("Test #58: Load disk, then reject - verify drops to reject pile")
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
    
    # Check if we can load
    print("\n2. PRE-LOAD CHECKS")
    print("-" * 20)
    print(f"is_ready(): {sm.is_ready()}")
    print(f"can_load_disk(): {sm.can_load_disk()}")
    
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
    
    # Reject the disk
    print("\n4. REJECTING DISK")
    print("-" * 20)
    print("Rejecting current disk...")
    start_time = time.time()
    
    success = sm.reject_current_disk()
    reject_time = time.time() - start_time
    
    print(f"Reject result: {success}")
    print(f"Time taken: {reject_time:.1f}s")
    print(f"State after reject: {sm.state}")
    print(f"is_ready(): {sm.is_ready()}")
    
    if not success or not sm.is_ready():
        print("❌ FAIL: Reject failed")
        exit(1)
    print("✅ Reject successful")
    
    # Verify final state
    print("\n5. FINAL STATE")
    print("-" * 20)
    print(f"Final state: {sm.state}")
    print(f"is_ready(): {sm.is_ready()}")
    
    print("\n" + "="*60)
    print("✅ TEST #58 COMPLETE: Load disk, then reject - SUCCESS!")
    print("✅ Disk successfully dropped to reject pile")
    print("="*60)
    
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()