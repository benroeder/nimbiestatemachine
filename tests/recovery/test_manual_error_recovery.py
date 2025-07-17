#!/usr/bin/env python3
"""Test error recovery using manual operations to create error states."""

import logging
import time
from nimbie import NimbieStateMachine  # Use old system for manual operations
from nimbie.pure_state_machine import NimbiePureStateMachine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

print("\n" + "="*80)
print("MANUAL ERROR RECOVERY TEST")
print("="*80)
print("Using manual operations to create error states, then test pure state machine recovery")

def test_lifted_disk_recovery():
    """Test recovery from lifted disk error state."""
    print("\n" + "="*60)
    print("TEST 1: Lifted Disk Recovery")
    print("="*60)
    
    # Use old system to create error state
    print("\n1. CREATING ERROR STATE (Lifted Disk)")
    print("-" * 30)
    old_sm = NimbieStateMachine("1", log_level=logging.WARNING)
    
    # Check if we have a disk available
    hw_state = old_sm.get_hardware_state()
    if not hw_state["disk_available"]:
        print("❌ No disk available - cannot test lifted disk recovery")
        return False
    
    print("Using manual operations to create lifted disk error state...")
    with old_sm.manual_operation():
        # Create error state: disk lifted but tray closed
        print("  Opening tray...")
        old_sm.manual_open_tray()
        time.sleep(1)
        
        print("  Placing disk...")
        old_sm.manual_place_disk()
        time.sleep(1)
        
        print("  Lifting disk...")
        old_sm.manual_lift_disk()
        time.sleep(1)
        
        print("  Closing tray with disk lifted...")
        old_sm.manual_close_tray()
        time.sleep(1)
        
        # Verify error state
        hw_state = old_sm.get_hardware_state()
        print(f"  Hardware state: {hw_state}")
        
        if hw_state["disk_lifted"] and not hw_state["tray_out"]:
            print("✅ Error state created: Disk lifted with tray closed")
        else:
            print("❌ Failed to create lifted disk error state")
            return False
    
    # Test pure state machine recovery
    print("\n2. TESTING PURE STATE MACHINE RECOVERY")
    print("-" * 30)
    
    # Create pure state machine
    pure_sm = NimbiePureStateMachine("1", log_level=logging.INFO)
    
    # Initialize - should handle the error state
    print("Testing initialization with lifted disk...")
    try:
        pure_sm.initialize()
        print(f"Initialization result: {pure_sm.state}")
        
        if pure_sm.state == 'ready':
            print("✅ Pure state machine successfully recovered from lifted disk")
            
            # Verify hardware is clean
            hw_state = pure_sm.hardware.get_state()
            print(f"Hardware state after recovery: {hw_state}")
            
            if not hw_state["disk_lifted"] and not hw_state["tray_out"]:
                print("✅ Hardware properly cleaned up")
                return True
            else:
                print("❌ Hardware not properly cleaned up")
                return False
        else:
            print(f"❌ Pure state machine failed to recover: {pure_sm.state}")
            return False
            
    except Exception as e:
        print(f"❌ Recovery failed: {type(e).__name__}: {e}")
        return False

def test_open_tray_recovery():
    """Test recovery from open tray error state."""
    print("\n" + "="*60)
    print("TEST 2: Open Tray Recovery")
    print("="*60)
    
    # Use old system to create error state
    print("\n1. CREATING ERROR STATE (Open Tray)")
    print("-" * 30)
    old_sm = NimbieStateMachine("1", log_level=logging.WARNING)
    
    print("Using manual operations to create open tray error state...")
    with old_sm.manual_operation():
        # Create error state: tray open
        print("  Opening tray...")
        old_sm.manual_open_tray()
        time.sleep(1)
        
        # Verify error state
        hw_state = old_sm.get_hardware_state()
        print(f"  Hardware state: {hw_state}")
        
        if hw_state["tray_out"]:
            print("✅ Error state created: Tray open")
        else:
            print("❌ Failed to create open tray error state")
            return False
    
    # Test pure state machine recovery
    print("\n2. TESTING PURE STATE MACHINE RECOVERY")
    print("-" * 30)
    
    # Create pure state machine
    pure_sm = NimbiePureStateMachine("1", log_level=logging.INFO)
    
    # Initialize - should handle the error state
    print("Testing initialization with open tray...")
    try:
        pure_sm.initialize()
        print(f"Initialization result: {pure_sm.state}")
        
        if pure_sm.state == 'ready':
            print("✅ Pure state machine successfully recovered from open tray")
            
            # Verify hardware is clean
            hw_state = pure_sm.hardware.get_state()
            print(f"Hardware state after recovery: {hw_state}")
            
            if not hw_state["tray_out"]:
                print("✅ Hardware properly cleaned up")
                return True
            else:
                print("❌ Hardware not properly cleaned up")
                return False
        else:
            print(f"❌ Pure state machine failed to recover: {pure_sm.state}")
            return False
            
    except Exception as e:
        print(f"❌ Recovery failed: {type(e).__name__}: {e}")
        return False

def test_disk_in_tray_recovery():
    """Test recovery from disk in open tray."""
    print("\n" + "="*60)
    print("TEST 3: Disk in Open Tray Recovery")
    print("="*60)
    
    # Use old system to create error state
    print("\n1. CREATING ERROR STATE (Disk in Open Tray)")
    print("-" * 30)
    old_sm = NimbieStateMachine("1", log_level=logging.WARNING)
    
    # Check if we have a disk available
    hw_state = old_sm.get_hardware_state()
    if not hw_state["disk_available"]:
        print("❌ No disk available - cannot test disk in tray recovery")
        return False
    
    print("Using manual operations to create disk in open tray error state...")
    with old_sm.manual_operation():
        # Create error state: disk in open tray
        print("  Opening tray...")
        old_sm.manual_open_tray()
        time.sleep(1)
        
        print("  Placing disk...")
        old_sm.manual_place_disk()
        time.sleep(1)
        
        # Verify error state
        hw_state = old_sm.get_hardware_state()
        print(f"  Hardware state: {hw_state}")
        
        if hw_state["disk_in_open_tray"] and hw_state["tray_out"]:
            print("✅ Error state created: Disk in open tray")
        else:
            print("❌ Failed to create disk in open tray error state")
            return False
    
    # Test pure state machine recovery
    print("\n2. TESTING PURE STATE MACHINE RECOVERY")
    print("-" * 30)
    
    # Create pure state machine
    pure_sm = NimbiePureStateMachine("1", log_level=logging.INFO)
    
    # Initialize - should handle the error state
    print("Testing initialization with disk in open tray...")
    try:
        pure_sm.initialize()
        print(f"Initialization result: {pure_sm.state}")
        
        if pure_sm.state == 'ready':
            print("✅ Pure state machine successfully recovered from disk in open tray")
            
            # Verify hardware is clean
            hw_state = pure_sm.hardware.get_state()
            print(f"Hardware state after recovery: {hw_state}")
            
            if not hw_state["disk_in_open_tray"] and not hw_state["tray_out"]:
                print("✅ Hardware properly cleaned up")
                return True
            else:
                print("❌ Hardware not properly cleaned up")
                return False
        else:
            print(f"❌ Pure state machine failed to recover: {pure_sm.state}")
            return False
            
    except Exception as e:
        print(f"❌ Recovery failed: {type(e).__name__}: {e}")
        return False

def main():
    """Run all error recovery tests."""
    print("Testing error recovery using manual operations...")
    
    results = []
    
    # Test 1: Lifted disk recovery
    try:
        results.append(("Lifted Disk Recovery", test_lifted_disk_recovery()))
    except Exception as e:
        print(f"❌ Lifted disk test failed: {e}")
        results.append(("Lifted Disk Recovery", False))
    
    # Test 2: Open tray recovery
    try:
        results.append(("Open Tray Recovery", test_open_tray_recovery()))
    except Exception as e:
        print(f"❌ Open tray test failed: {e}")
        results.append(("Open Tray Recovery", False))
    
    # Test 3: Disk in tray recovery
    try:
        results.append(("Disk in Tray Recovery", test_disk_in_tray_recovery()))
    except Exception as e:
        print(f"❌ Disk in tray test failed: {e}")
        results.append(("Disk in Tray Recovery", False))
    
    # Summary
    print("\n" + "="*80)
    print("MANUAL ERROR RECOVERY TEST SUMMARY")
    print("="*80)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All error recovery tests passed!")
        return True
    else:
        print("❌ Some error recovery tests failed")
        return False

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test suite failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        exit(1)