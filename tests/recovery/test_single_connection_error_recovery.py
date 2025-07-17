#!/usr/bin/env python3
"""Test error recovery using single connection to avoid USB conflicts."""

import logging
import time
from nimbie import NimbieStateMachine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

print("\n" + "="*80)
print("SINGLE CONNECTION ERROR RECOVERY TEST")
print("="*80)
print("Testing error recovery by manually creating error states")

def test_lifted_disk_recovery():
    """Test recovery from lifted disk error state."""
    print("\n" + "="*60)
    print("TEST 1: Lifted Disk Recovery")
    print("="*60)
    
    # Create single connection
    sm = NimbieStateMachine("1", log_level=logging.INFO)
    
    # Check if we have a disk available
    hw_state = sm.get_hardware_state()
    print(f"Initial hardware state: {hw_state}")
    
    if not hw_state["disk_available"]:
        print("❌ No disk available - cannot test lifted disk recovery")
        return False
    
    print("\n1. CREATING ERROR STATE (Lifted Disk)")
    print("-" * 40)
    
    print("Using manual operations to create lifted disk error state...")
    try:
        with sm.manual_operation():
            # Create error state: disk lifted but tray closed
            print("  Opening tray...")
            sm.manual_open_tray()
            time.sleep(1)
            
            print("  Placing disk...")
            sm.manual_place_disk()
            time.sleep(1)
            
            print("  Lifting disk...")
            sm.manual_lift_disk()
            time.sleep(1)
            
            print("  Closing tray with disk lifted...")
            sm.manual_close_tray()
            time.sleep(1)
            
            # Verify error state
            hw_state = sm.get_hardware_state()
            print(f"  Hardware state after error creation: {hw_state}")
            
            if hw_state["disk_lifted"] and not hw_state["tray_out"]:
                print("✅ Error state created: Disk lifted with tray closed")
            else:
                print("❌ Failed to create lifted disk error state")
                return False
    except Exception as e:
        print(f"❌ Failed to create error state: {e}")
        return False
    
    print("\n2. TESTING RECOVERY USING SAME CONNECTION")
    print("-" * 40)
    
    # Test recovery using the same state machine
    print("Testing recovery from lifted disk state...")
    try:
        # Check if we're in error state
        hw_state = sm.get_hardware_state()
        print(f"Hardware state before recovery: {hw_state}")
        
        if hw_state["disk_lifted"]:
            print("Attempting recovery...")
            with sm.manual_operation():
                # Recovery sequence
                print("  Ensuring tray is closed...")
                if sm.get_hardware_state()["tray_out"]:
                    sm.manual_close_tray()
                    time.sleep(1)
                
                print("  Dropping lifted disk...")
                sm.manual_accept_disk()  # Drop to accept pile
                time.sleep(1)
                
                print("  Resetting state to idle...")
                sm.manual_set_state("idle")
                
                # Verify recovery
                hw_state = sm.get_hardware_state()
                print(f"  Hardware state after recovery: {hw_state}")
                
                if not hw_state["disk_lifted"] and not hw_state["tray_out"]:
                    print("✅ Recovery successful: Hardware cleaned up")
                    return True
                else:
                    print("❌ Recovery incomplete: Hardware not clean")
                    return False
        else:
            print("❌ Not in lifted disk error state")
            return False
            
    except Exception as e:
        print(f"❌ Recovery failed: {type(e).__name__}: {e}")
        return False

def test_open_tray_recovery():
    """Test recovery from open tray error state."""
    print("\n" + "="*60)
    print("TEST 2: Open Tray Recovery")
    print("="*60)
    
    # Create single connection
    sm = NimbieStateMachine("1", log_level=logging.INFO)
    
    print("\n1. CREATING ERROR STATE (Open Tray)")
    print("-" * 40)
    
    print("Using manual operations to create open tray error state...")
    try:
        with sm.manual_operation():
            # Create error state: tray open
            print("  Opening tray...")
            sm.manual_open_tray()
            time.sleep(1)
            
            # Verify error state
            hw_state = sm.get_hardware_state()
            print(f"  Hardware state after error creation: {hw_state}")
            
            if hw_state["tray_out"]:
                print("✅ Error state created: Tray open")
            else:
                print("❌ Failed to create open tray error state")
                return False
    except Exception as e:
        print(f"❌ Failed to create error state: {e}")
        return False
    
    print("\n2. TESTING RECOVERY USING SAME CONNECTION")
    print("-" * 40)
    
    # Test recovery using the same state machine
    print("Testing recovery from open tray state...")
    try:
        # Check if we're in error state
        hw_state = sm.get_hardware_state()
        print(f"Hardware state before recovery: {hw_state}")
        
        if hw_state["tray_out"]:
            print("Attempting recovery...")
            with sm.manual_operation():
                # Recovery sequence
                print("  Closing tray...")
                sm.manual_close_tray()
                time.sleep(1)
                
                print("  Resetting state to idle...")
                sm.manual_set_state("idle")
                
                # Verify recovery
                hw_state = sm.get_hardware_state()
                print(f"  Hardware state after recovery: {hw_state}")
                
                if not hw_state["tray_out"]:
                    print("✅ Recovery successful: Tray closed")
                    return True
                else:
                    print("❌ Recovery incomplete: Tray still open")
                    return False
        else:
            print("❌ Not in open tray error state")
            return False
            
    except Exception as e:
        print(f"❌ Recovery failed: {type(e).__name__}: {e}")
        return False

def test_disk_in_tray_recovery():
    """Test recovery from disk in open tray."""
    print("\n" + "="*60)
    print("TEST 3: Disk in Open Tray Recovery")
    print("="*60)
    
    # Create single connection
    sm = NimbieStateMachine("1", log_level=logging.INFO)
    
    # Check if we have a disk available
    hw_state = sm.get_hardware_state()
    if not hw_state["disk_available"]:
        print("❌ No disk available - cannot test disk in tray recovery")
        return False
    
    print("\n1. CREATING ERROR STATE (Disk in Open Tray)")
    print("-" * 40)
    
    print("Using manual operations to create disk in open tray error state...")
    try:
        with sm.manual_operation():
            # Create error state: disk in open tray
            print("  Opening tray...")
            sm.manual_open_tray()
            time.sleep(1)
            
            print("  Placing disk...")
            sm.manual_place_disk()
            time.sleep(1)
            
            # Verify error state
            hw_state = sm.get_hardware_state()
            print(f"  Hardware state after error creation: {hw_state}")
            
            if hw_state["disk_in_open_tray"] and hw_state["tray_out"]:
                print("✅ Error state created: Disk in open tray")
            else:
                print("❌ Failed to create disk in open tray error state")
                return False
    except Exception as e:
        print(f"❌ Failed to create error state: {e}")
        return False
    
    print("\n2. TESTING RECOVERY USING SAME CONNECTION")
    print("-" * 40)
    
    # Test recovery using the same state machine
    print("Testing recovery from disk in open tray state...")
    try:
        # Check if we're in error state
        hw_state = sm.get_hardware_state()
        print(f"Hardware state before recovery: {hw_state}")
        
        if hw_state["disk_in_open_tray"] and hw_state["tray_out"]:
            print("Attempting recovery...")
            with sm.manual_operation():
                # Recovery sequence
                print("  Lifting disk from tray...")
                sm.manual_lift_disk()
                time.sleep(1)
                
                print("  Closing tray...")
                sm.manual_close_tray()
                time.sleep(1)
                
                print("  Dropping disk to accept pile...")
                sm.manual_accept_disk()
                time.sleep(1)
                
                print("  Resetting state to idle...")
                sm.manual_set_state("idle")
                
                # Verify recovery
                hw_state = sm.get_hardware_state()
                print(f"  Hardware state after recovery: {hw_state}")
                
                if not hw_state["disk_in_open_tray"] and not hw_state["tray_out"] and not hw_state["disk_lifted"]:
                    print("✅ Recovery successful: Hardware cleaned up")
                    return True
                else:
                    print("❌ Recovery incomplete: Hardware not clean")
                    return False
        else:
            print("❌ Not in disk in open tray error state")
            return False
            
    except Exception as e:
        print(f"❌ Recovery failed: {type(e).__name__}: {e}")
        return False

def main():
    """Run all error recovery tests."""
    print("Testing error recovery using single connection...")
    
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
    print("SINGLE CONNECTION ERROR RECOVERY TEST SUMMARY")
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