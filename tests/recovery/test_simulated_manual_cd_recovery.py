#!/usr/bin/env python3
"""Test recovery from simulated manual CD insertion (automated version)."""

import logging
import time
import sys
from nimbie import NimbieStateMachine
from nimbie.pure_state_machine import NimbiePureStateMachine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def create_manual_cd_state():
    """Simulate a manually inserted CD by bypassing Nimbie's tracking."""
    print("=" * 60)
    print("STEP 1: SIMULATING MANUAL CD INSERTION")
    print("=" * 60)
    
    print("Creating a scenario that simulates manual CD insertion...")
    old_sm = None
    try:
        # Create old state machine connection
        old_sm = NimbieStateMachine("1", log_level=logging.INFO)
        
        # Check initial state
        hw_state = old_sm.get_hardware_state()
        print(f"Initial hardware state: {hw_state}")
        
        if not hw_state["disk_available"]:
            print("❌ No disk available - cannot simulate manual CD insertion")
            return False
        
        # Use manual operations to create the scenario
        with old_sm.manual_operation():
            # This simulates what happens when a user manually inserts a CD:
            # 1. Open tray
            # 2. User puts CD directly on the drive tray (not through Nimbie)
            # 3. Close tray
            
            print("  Opening tray...")
            old_sm.manual_open_tray()
            time.sleep(1)
            
            print("  Placing disk using Nimbie (simulating manual placement)...")
            old_sm.manual_place_disk()
            time.sleep(2)
            
            # Now close the tray, but the disk position might not be
            # exactly where Nimbie expects it for a normal operation
            print("  Closing tray with disk...")
            old_sm.manual_close_tray()
            time.sleep(2)
            
            # In a real manual insertion, the disk would be in the drive
            # but Nimbie's internal tracking might be confused
            hw_state = old_sm.get_hardware_state()
            print(f"Hardware state after simulated manual insertion: {hw_state}")
            
            # Reset state machine state to simulate confusion
            old_sm.manual_set_state("idle")
            print("  Reset state machine to idle (simulating fresh start)")
            
            return True
                
    except Exception as e:
        print(f"❌ Failed to create manual CD state: {e}")
        return False
    finally:
        # Explicitly close connection
        if old_sm:
            try:
                old_sm.close()
                print("Old state machine connection closed")
            except Exception as e:
                print(f"Error closing old state machine: {e}")

def test_pure_state_machine_recovery():
    """Test pure state machine recovery from manual CD state."""
    print("\n" + "=" * 60)
    print("STEP 2: TESTING PURE STATE MACHINE RECOVERY")
    print("=" * 60)
    
    print("Creating new pure state machine connection...")
    print("This simulates starting the Nimbie system fresh after a manual CD insertion")
    
    try:
        # Create new pure state machine with fresh connection
        pure_sm = NimbiePureStateMachine(target_drive="1", log_level=logging.INFO)
        
        # Check hardware state before initialization
        hw_state = pure_sm.hardware.get_state()
        print(f"\nHardware state before initialization: {hw_state}")
        
        # Test initialization sequence
        print("\nTesting initialization sequence...")
        print("The pure state machine should detect and handle the manually inserted CD")
        
        # Initialize - this should detect the unusual state
        success = pure_sm.initialize()
        
        print(f"\nInitialization result: {success}")
        print(f"Final state machine state: {pure_sm.state}")
        
        # Check final hardware state
        hw_state = pure_sm.hardware.get_state()
        print(f"Final hardware state: {hw_state}")
        
        if success and pure_sm.state == "ready":
            print("\n✅ Recovery successful: System handled manual CD and is ready")
            return True
        elif pure_sm.state == "error":
            print("\n⚠️  System entered error state")
            print("This is expected if the manually inserted CD cannot be handled automatically")
            
            # Check if tray is open for manual intervention
            if hw_state["tray_out"]:
                print("Tray is open - manual removal is possible")
            
            return "error"
        else:
            print(f"\n❌ Unexpected result: success={success}, state={pure_sm.state}")
            return False
            
    except Exception as e:
        print(f"❌ Pure state machine recovery failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up pure state machine connection
        if 'pure_sm' in locals():
            try:
                pure_sm.close()
                print("Pure state machine connection closed")
            except:
                pass

def main():
    """Main test function."""
    print("SIMULATED MANUAL CD INSERTION RECOVERY TEST")
    print("=" * 80)
    print("Testing recovery from simulated manual CD insertion")
    print("This tests what happens when a CD is inserted outside of Nimbie's control")
    
    # Step 1: Create manual CD state
    state_created = create_manual_cd_state()
    if not state_created:
        print("\n❌ FAILED: Could not create manual CD state")
        return False
    
    # Brief pause to ensure connection is fully closed
    print("\nWaiting for connection to close completely...")
    time.sleep(10)  # Longer wait to ensure USB is fully released
    
    # Step 2: Test pure state machine recovery
    recovery_result = test_pure_state_machine_recovery()
    
    # Summary
    print("\n" + "=" * 80)
    print("SIMULATED MANUAL CD RECOVERY TEST SUMMARY")
    print("=" * 80)
    
    if recovery_result == True:
        print("✅ SUCCESS: Pure state machine successfully recovered from manual CD insertion")
        print("✅ The system can handle CDs that were manually placed")
        return True
    elif recovery_result == "error":
        print("⚠️  EXPECTED BEHAVIOR: System correctly identified manual CD situation")
        print("⚠️  Manual intervention required - this is a hardware limitation")
        print("\nNOTE: When CDs are inserted manually (not through Nimbie's mechanism),")
        print("      the system may not be able to handle them automatically.")
        return False
    else:
        print("❌ FAILED: Pure state machine could not handle manual CD insertion")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)