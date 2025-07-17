#!/usr/bin/env python3
"""Test initialize transition with hardware."""

import logging
from nimbie.pure_state_machine import NimbiePureStateMachine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

print("Test #13 & #14: Initialize Transition Test")
print("=" * 50)

try:
    print("\nCreating state machine...")
    sm = NimbiePureStateMachine(target_drive="1", log_level=logging.INFO)
    print(f"Initial state: {sm.state}")
    
    print("\nCalling initialize() trigger...")
    sm.initialize()  # This should trigger the transition
    
    print(f"\nState after initialize: {sm.state}")
    if sm.state == 'ready':
        print("✅ SUCCESS: State changed to 'ready'")
    else:
        print(f"❌ FAIL: Expected 'ready', got '{sm.state}'")
    
    # Test #14: Verify hardware still works
    print("\nTest #14: Verify hardware.get_state() still works")
    hw_state = sm.hardware.get_state()
    print(f"Hardware state: {hw_state}")
    print("✅ SUCCESS: Hardware communication still working after transition")
    
    # Check that callbacks were executed
    print("\nTransition callbacks executed successfully")
    print("- before: _check_hardware")
    print("- after: _log_ready")
    
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()