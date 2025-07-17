#!/usr/bin/env python3
"""Test pure state machine with real hardware."""

import logging
from nimbie.pure_state_machine import NimbiePureStateMachine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

print("Test #9: Hardware Connection Test")
print("=" * 50)

try:
    print("\nCreating NimbiePureStateMachine with hardware...")
    sm = NimbiePureStateMachine(target_drive="1", log_level=logging.INFO)
    print("✅ SUCCESS: State machine created with hardware connection")
    
    # Test #10: Check initial state
    print(f"\nTest #10: Initial state check")
    print(f"Current state: {sm.state}")
    if sm.state == 'initializing':
        print("✅ SUCCESS: Initial state is 'initializing'")
    else:
        print(f"❌ FAIL: Expected 'initializing', got '{sm.state}'")
    
    # Try to read hardware state
    print("\nReading hardware state...")
    hw_state = sm.hardware.get_state()
    print(f"Hardware state: {hw_state}")
    print("✅ Hardware communication working")
    
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")
    print("\nMake sure:")
    print("- Nimbie is connected via USB")
    print("- Nimbie is powered on")
    print("- No other program is using the device")