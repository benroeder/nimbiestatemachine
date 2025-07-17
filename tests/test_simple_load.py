#!/usr/bin/env python3
"""Simple test of load operation after proper init."""

import logging
import time
from nimbie.pure_state_machine import NimbiePureStateMachine

logging.basicConfig(level=logging.WARNING)  # Less verbose

print("Simple Load Test")
print("=" * 50)

try:
    # Create and initialize
    print("1. Initializing...")
    sm = NimbiePureStateMachine(target_drive="1", log_level=logging.WARNING)
    sm.initialize()
    print(f"   State: {sm.state}")
    
    # Check hardware
    hw_state = sm.hardware.get_state()
    print(f"\n2. Hardware state:")
    print(f"   disk_available: {hw_state['disk_available']}")
    print(f"   tray_out: {hw_state['tray_out']}")
    
    if not hw_state['disk_available']:
        print("\n❌ No disk available")
        exit(1)
    
    # Load disk
    print(f"\n3. Loading disk...")
    start = time.time()
    sm.load_disk()
    
    # Wait for loading to complete
    while sm.state != 'processing' and time.time() - start < 60:
        if sm.state == 'error':
            print(f"   ❌ Error state!")
            break
        time.sleep(0.5)
    
    elapsed = time.time() - start
    print(f"   Final state: {sm.state} (after {elapsed:.1f}s)")
    
    # Check final hardware state
    hw_state = sm.hardware.get_state()
    print(f"\n4. Final hardware:")
    print(f"   tray_out: {hw_state['tray_out']}")
    print(f"   disk_in_open_tray: {hw_state.get('disk_in_open_tray', 'N/A')}")
    
    if sm.state == 'processing':
        print("\n✅ SUCCESS: Disk loaded!")
    else:
        print(f"\n❌ FAIL: Expected 'processing', got '{sm.state}'")
        
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {e}")