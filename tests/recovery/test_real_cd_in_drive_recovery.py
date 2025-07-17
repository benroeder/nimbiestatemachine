#!/usr/bin/env python3
"""Test recovery when a real CD is manually inserted in the drive."""

import logging
import time
import sys
from nimbie.pure_state_machine import NimbiePureStateMachine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def main():
    """Test pure state machine recovery with manually inserted CD."""
    print("REAL CD IN DRIVE RECOVERY TEST")
    print("=" * 80)
    print("Testing recovery when a CD is manually inserted in the drive")
    print("\nThis simulates the scenario where:")
    print("- A user manually inserted a CD into the drive")
    print("- The Nimbie system was not involved in loading the disk")
    print("- The pure state machine needs to detect and handle this situation")
    
    print("\n" + "=" * 60)
    print("INSTRUCTIONS")
    print("=" * 60)
    print("1. Please manually insert a CD into the drive")
    print("2. Make sure the tray is closed")
    print("3. Press Enter when ready...")
    input()
    
    print("\n" + "=" * 60)
    print("TESTING PURE STATE MACHINE RECOVERY")
    print("=" * 60)
    
    print("Creating pure state machine connection...")
    try:
        # Create pure state machine
        pure_sm = NimbiePureStateMachine(target_drive="1", log_level=logging.INFO)
        
        # Check hardware state before initialization
        hw_state = pure_sm.hardware.get_state()
        print(f"Hardware state before initialization: {hw_state}")
        
        # Test initialization sequence
        print("\nRunning initialization sequence...")
        print("The pure state machine should detect the manually inserted CD")
        
        # Initialize - see how it handles the manually inserted disk
        success = pure_sm.initialize()
        
        if success:
            print("\n✅ Initialization completed successfully")
            
            # Check final state
            hw_state = pure_sm.hardware.get_state()
            print(f"Hardware state after initialization: {hw_state}")
            print(f"Pure state machine state: {pure_sm.state}")
            
            if pure_sm.state == "ready":
                print("\n✅ Recovery successful: System is ready despite manual CD insertion")
                return True
            else:
                print(f"\n⚠️  System ended in state: {pure_sm.state}")
                return False
        else:
            print("\n❌ Initialization failed")
            print(f"Pure state machine state: {pure_sm.state}")
            
            # Check if it's in error state
            if pure_sm.state == "error":
                print("\n⚠️  System correctly identified unrecoverable situation")
                print("Manual intervention required to remove the CD")
                
                # Check hardware state
                hw_state = pure_sm.hardware.get_state()
                print(f"\nFinal hardware state: {hw_state}")
                
                if hw_state["tray_out"]:
                    print("Tray is open - manual removal of CD is possible")
                else:
                    print("Tray is closed - may need manual eject")
                
                return False
            else:
                print(f"\nUnexpected state: {pure_sm.state}")
                return False
            
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def cleanup():
    """Clean up after test."""
    print("\n" + "=" * 60)
    print("CLEANUP")
    print("=" * 60)
    
    try:
        from nimbie import NimbieDriver
        d = NimbieDriver("1")
        state = d.get_state()
        
        print(f"Current state: {state}")
        
        if state["tray_out"]:
            print("Please remove any CD from the tray")
            print("Press Enter when done...")
            input()
            
            print("Closing tray...")
            d.close_tray()
            time.sleep(2)
        
        print("Cleanup complete")
        
    except Exception as e:
        print(f"Cleanup failed: {e}")

if __name__ == "__main__":
    try:
        success = main()
        
        # Always run cleanup
        cleanup()
        
        # Summary
        print("\n" + "=" * 80)
        print("REAL CD IN DRIVE RECOVERY TEST SUMMARY")
        print("=" * 80)
        
        if success:
            print("✅ The pure state machine successfully handled a manually inserted CD")
        else:
            print("❌ The pure state machine could not automatically handle a manually inserted CD")
            print("⚠️  This is expected behavior - manual intervention is required")
            print("\nNOTE: The Nimbie hardware cannot reliably handle CDs that were not")
            print("      loaded through its own mechanism. This is a hardware limitation.")
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"\n❌ Test failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)