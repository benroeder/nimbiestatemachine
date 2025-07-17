#!/usr/bin/env python3
"""Test that disk is in drive when in processing state."""

import logging
from nimbie.pure_state_machine import NimbiePureStateMachine

logging.basicConfig(level=logging.WARNING)

print("\nTest #43: Verify disk is in drive in processing state")
print("=" * 50)

try:
    # Create and initialize
    print("1. Initializing state machine...")
    sm = NimbiePureStateMachine(target_drive="1", log_level=logging.WARNING)
    sm.initialize()
    print(f"   State: {sm.state}")
    
    # Check if disk available
    hw_state = sm.hardware.get_state()
    if not hw_state['disk_available']:
        print("\n❌ No disk available. Please add a disk to the queue.")
        exit(1)
    
    # Load disk
    print("\n2. Loading disk...")
    sm.load_disk()
    
    # Verify we're in processing state
    print(f"\n3. Current state: {sm.state}")
    if sm.state != 'processing':
        print(f"❌ FAIL: Expected 'processing' state, got '{sm.state}'")
        exit(1)
    
    print("✅ State is 'processing'")
    
    # Check hardware state
    hw_state = sm.hardware.get_state()
    print(f"\n4. Hardware state in processing:")
    print(f"   tray_out: {hw_state['tray_out']}")
    print(f"   disk_in_open_tray: {hw_state.get('disk_in_open_tray', 'N/A')}")
    print(f"   disk_available: {hw_state['disk_available']}")
    
    # Verify disk is in drive (tray closed, disk not available in queue)
    if not hw_state['tray_out'] and not hw_state['disk_available']:
        print("\n✅ SUCCESS: Disk is in the drive (tray closed, disk not in queue)")
    else:
        print("\n❌ FAIL: Disk doesn't appear to be in drive")
        
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()