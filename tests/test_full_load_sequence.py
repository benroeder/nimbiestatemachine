#!/usr/bin/env python3
"""Test full load sequence with real disk."""

import logging
import time
from nimbie.pure_state_machine import NimbiePureStateMachine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

print("\nTest #41: Full load sequence with real disk")
print("=" * 50)
print("This test runs the complete loading sequence:")
print("1. Tray opens")
print("2. Disk is placed on tray") 
print("3. Tray closes with disk")
print("4. State transitions to processing")
print()

try:
    # Create and initialize state machine
    print("Creating and initializing state machine...")
    sm = NimbiePureStateMachine(target_drive="1", log_level=logging.INFO)
    sm.initialize()
    
    # Check if disk is available
    hw_state = sm.hardware.get_state()
    if not hw_state['disk_available']:
        print("No disk available in queue. Cannot test.")
        print("Please add a disk and run again.")
        exit(1)
    
    print(f"\nInitial hardware state:")
    print(f"  disk_available: {hw_state['disk_available']}")
    print(f"  tray_out: {hw_state['tray_out']}")
    print(f"  disk_in_open_tray: {hw_state['disk_in_open_tray']}")
    
    # Start loading process
    print("\n🎯 Starting load_disk - watch the hardware...")
    start_time = time.time()
    sm.load_disk()
    print(f"Initial state: {sm.state}")
    
    # Monitor state changes
    print("\nMonitoring state changes...")
    max_wait = 30  # seconds
    last_state = sm.state
    states_seen = [last_state]
    
    while time.time() - start_time < max_wait:
        current_state = sm.state
        if current_state != last_state:
            elapsed = time.time() - start_time
            print(f"[{elapsed:5.1f}s] {last_state} → {current_state}")
            last_state = current_state
            states_seen.append(current_state)
            
        if current_state == 'processing':
            print(f"\n✅ SUCCESS: Disk loaded successfully in {time.time() - start_time:.1f} seconds!")
            break
            
        if current_state == 'error':
            print("\n❌ FAIL: Entered error state")
            break
            
        time.sleep(0.1)
    else:
        print(f"\n❌ Timeout after {max_wait} seconds")
    
    # Final hardware state
    hw_state = sm.hardware.get_state()
    print(f"\nFinal hardware state:")
    print(f"  disk_available: {hw_state['disk_available']}")
    print(f"  tray_out: {hw_state['tray_out']}")
    print(f"  disk_in_open_tray: {hw_state['disk_in_open_tray']}")
    print(f"  disk_lifted: {hw_state['disk_lifted']}")
    
    print(f"\nStates traversed: {' → '.join(states_seen)}")
    
    # Expected sequence
    expected = [
        'loading_opening_tray',
        'loading_waiting_tray_open', 
        'loading_placing_disk',
        'loading_waiting_disk_placed',
        'loading_closing_tray',
        'loading_waiting_tray_closed',
        'processing'
    ]
    
    if states_seen == expected:
        print("✅ All states traversed in correct order!")
    else:
        print("❌ State sequence doesn't match expected")
        print(f"Expected: {expected}")
        print(f"Got:      {states_seen}")
        
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()