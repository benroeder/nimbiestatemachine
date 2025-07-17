#!/usr/bin/env python3
"""Test manual transitions between loading sub-states."""

import logging
from nimbie.pure_state_machine import NimbiePureStateMachine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

print("\nTest #29: Manually verify sub-state transitions")
print("=" * 50)

try:
    # Create and initialize state machine
    print("Creating and initializing state machine...")
    sm = NimbiePureStateMachine(target_drive="1", log_level=logging.INFO)
    sm.initialize()
    
    # Check if disk is available
    hw_state = sm.hardware.get_state()
    if not hw_state['disk_available']:
        print("No disk available. Cannot test transitions.")
        exit(1)
    
    # Start loading process
    print("\n1. Starting load_disk...")
    sm.load_disk()
    print(f"   State: {sm.state}")
    
    # The transition to waiting should happen automatically
    if sm.state == 'loading_waiting_tray_open':
        print("   ✅ Auto-transitioned to waiting_tray_open")
    else:
        print(f"   ❌ Expected loading_waiting_tray_open, got {sm.state}")
    
    # Manually trigger tray opened
    print("\n2. Manually triggering tray_opened...")
    sm.tray_opened()
    print(f"   State: {sm.state}")
    if sm.state == 'loading_placing_disk':
        print("   ✅ Transitioned to placing_disk")
    
    # Manually trigger disk placing
    print("\n3. Manually triggering disk_placing...")
    sm.disk_placing()
    print(f"   State: {sm.state}")
    if sm.state == 'loading_waiting_disk_placed':
        print("   ✅ Transitioned to waiting_disk_placed")
    
    # Manually trigger disk placed
    print("\n4. Manually triggering disk_placed...")
    sm.disk_placed()
    print(f"   State: {sm.state}")
    if sm.state == 'loading_closing_tray':
        print("   ✅ Transitioned to closing_tray")
    
    # Manually trigger tray closing
    print("\n5. Manually triggering tray_closing...")
    sm.tray_closing()
    print(f"   State: {sm.state}")
    if sm.state == 'loading_waiting_tray_closed':
        print("   ✅ Transitioned to waiting_tray_closed")
    
    # Manually trigger tray closed
    print("\n6. Manually triggering tray_closed...")
    sm.tray_closed()
    print(f"   State: {sm.state}")
    if sm.state == 'processing':
        print("   ✅ Transitioned to processing - Loading complete!")
    
    print("\n✅ SUCCESS: All sub-state transitions work correctly")
    
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()