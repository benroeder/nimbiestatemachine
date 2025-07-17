#!/usr/bin/env python3
"""Test error recovery with proper cleanup between tests."""

import logging
import time
from nimbie import NimbieStateMachine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def ensure_clean_state(sm):
    """Ensure hardware is in clean state before test."""
    print("  Ensuring clean state...")
    try:
        with sm.manual_operation():
            hw_state = sm.get_hardware_state()
            print(f"    Current state: {hw_state}")
            
            # If disk is lifted, drop it
            if hw_state["disk_lifted"]:
                print("    Dropping lifted disk...")
                if hw_state["tray_out"]:
                    sm.manual_close_tray()
                    time.sleep(1)
                sm.manual_accept_disk()
                time.sleep(1)
            
            # If tray is open, close it
            if sm.get_hardware_state()["tray_out"]:
                print("    Closing tray...")
                sm.manual_close_tray()
                time.sleep(1)
            
            # Reset state to idle
            sm.manual_set_state("idle")
            time.sleep(1)
            
            # Verify clean state
            hw_state = sm.get_hardware_state()
            print(f"    Clean state: {hw_state}")
            
            if not hw_state["disk_lifted"] and not hw_state["tray_out"]:
                print("    ✅ Hardware is clean")
                return True
            else:
                print("    ❌ Hardware still not clean")
                return False
                
    except Exception as e:
        print(f"    ❌ Cleanup failed: {e}")
        return False

def main():
    """Run all error recovery tests with proper cleanup."""
    print("\n" + "="*80)
    print("ERROR RECOVERY TEST WITH PROPER CLEANUP")
    print("="*80)
    print("Testing error recovery with cleanup between tests")
    
    # Create ONE connection for all tests
    sm = NimbieStateMachine("1", log_level=logging.INFO)
    
    results = []
    
    # Test 1: Open tray recovery (simplest test first)
    print("\n" + "="*60)
    print("TEST 1: Open Tray Recovery")
    print("="*60)
    
    # Ensure clean state
    if not ensure_clean_state(sm):
        print("❌ Failed to ensure clean state for test 1")
        results.append(("Open Tray Recovery", False))
    else:
        try:
            result = test_open_tray_recovery(sm)
            results.append(("Open Tray Recovery", result))
        except Exception as e:
            print(f"❌ Open tray test failed: {e}")
            results.append(("Open Tray Recovery", False))
    
    # Test 2: Disk in tray recovery
    print("\n" + "="*60)
    print("TEST 2: Disk in Open Tray Recovery")
    print("="*60)
    
    # Ensure clean state
    if not ensure_clean_state(sm):
        print("❌ Failed to ensure clean state for test 2")
        results.append(("Disk in Tray Recovery", False))
    else:
        try:
            result = test_disk_in_tray_recovery(sm)
            results.append(("Disk in Tray Recovery", result))
        except Exception as e:
            print(f"❌ Disk in tray test failed: {e}")
            results.append(("Disk in Tray Recovery", False))
    
    # Test 3: Lifted disk recovery
    print("\n" + "="*60)
    print("TEST 3: Lifted Disk Recovery")
    print("="*60)
    
    # Ensure clean state
    if not ensure_clean_state(sm):
        print("❌ Failed to ensure clean state for test 3")
        results.append(("Lifted Disk Recovery", False))
    else:
        try:
            result = test_lifted_disk_recovery(sm)
            results.append(("Lifted Disk Recovery", result))
        except Exception as e:
            print(f"❌ Lifted disk test failed: {e}")
            results.append(("Lifted Disk Recovery", False))
    
    # Final cleanup
    print("\n" + "="*60)
    print("FINAL CLEANUP")
    print("="*60)
    ensure_clean_state(sm)
    
    # Summary
    print("\n" + "="*80)
    print("ERROR RECOVERY TEST SUMMARY")
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

def test_open_tray_recovery(sm):
    """Test recovery from open tray error state."""
    
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
    
    print("\n2. TESTING RECOVERY")
    print("-" * 40)
    
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

def test_disk_in_tray_recovery(sm):
    """Test recovery from disk in open tray."""
    
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
            time.sleep(2)  # Give more time for disk placement
            
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
    
    print("\n2. TESTING RECOVERY")
    print("-" * 40)
    
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

def test_lifted_disk_recovery(sm):
    """Test recovery from lifted disk error state."""
    
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
            time.sleep(2)  # Give more time for disk placement
            
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
    
    print("\n2. TESTING RECOVERY")
    print("-" * 40)
    
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

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test suite failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        exit(1)