#!/usr/bin/env python3
"""Test initialization with tray already open."""

import logging
import time
from nimbie.pure_state_machine import NimbiePureStateMachine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

print("\nTest #84: Start with disk in open tray - verify cleared")
print("=" * 50)
print("Current hardware state: Tray is open")
print("Expected: Initialization should handle open tray and transition to ready")
print()

try:
    # Create state machine (starts in initializing)
    print("Creating state machine...")
    sm = NimbiePureStateMachine(target_drive="1", log_level=logging.INFO)
    print(f"Initial state: {sm.state}")
    
    # Initialize - should handle open tray
    print("\nCalling initialize()...")
    start_time = time.time()
    sm.initialize()
    
    # Monitor state changes
    print("\nMonitoring initialization sequence...")
    max_wait = 60  # seconds
    last_state = sm.state
    
    while time.time() - start_time < max_wait:
        current_state = sm.state
        if current_state != last_state:
            elapsed = time.time() - start_time
            print(f"[{elapsed:5.1f}s] {last_state} → {current_state}")
            last_state = current_state
            
        if current_state == 'ready':
            print(f"\n✅ SUCCESS: Reached ready state in {time.time() - start_time:.1f} seconds!")
            break
            
        if current_state == 'error':
            print("\n❌ FAIL: Entered error state")
            break
            
        time.sleep(0.1)
    else:
        print(f"\n❌ Timeout after {max_wait} seconds")
        print(f"Final state: {sm.state}")
    
    # Check final hardware state
    hw_state = sm.hardware.get_state()
    print(f"\nFinal hardware state:")
    print(f"  disk_available: {hw_state['disk_available']}")
    print(f"  tray_out: {hw_state['tray_out']}")
    print(f"  disk_in_open_tray: {hw_state['disk_in_open_tray']}")
    print(f"  disk_lifted: {hw_state['disk_lifted']}")
    
    # Verify tray is closed
    if not hw_state['tray_out']:
        print("✅ Tray successfully closed")
    else:
        print("❌ Tray is still open")
        
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()