#!/usr/bin/env python3
"""Test tray open recovery with separate connections."""

import logging
import time
import sys
from nimbie import NimbieStateMachine
from nimbie.pure_state_machine import NimbiePureStateMachine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def create_error_state():
    """Create tray open error state using old system, then close connection."""
    print("=" * 60)
    print("STEP 1: CREATING ERROR STATE (Tray Open)")
    print("=" * 60)
    
    print("Using old state machine to create tray open error state...")
    old_sm = None
    try:
        # Create old state machine connection
        old_sm = NimbieStateMachine("1", log_level=logging.INFO)
        
        # Use manual operations to create error state
        with old_sm.manual_operation():
            # Ensure clean start
            hw_state = old_sm.get_hardware_state()
            print(f"Initial hardware state: {hw_state}")
            
            # Create error state: tray open
            print("  Opening tray...")
            old_sm.manual_open_tray()
            time.sleep(1)
            
            # Verify error state created
            hw_state = old_sm.get_hardware_state()
            print(f"Hardware state after error creation: {hw_state}")
            
            if hw_state["tray_out"]:
                print("✅ Error state created successfully: Tray is open")
                return True
            else:
                print("❌ Failed to create tray open error state")
                return False
                
    except Exception as e:
        print(f"❌ Failed to create error state: {e}")
        return False
    finally:
        # Explicitly close connection
        if old_sm:
            try:
                # Close the underlying hardware connection
                if hasattr(old_sm, 'hardware') and old_sm.hardware:
                    if hasattr(old_sm.hardware, 'dev') and old_sm.hardware.dev:
                        # Release the USB interface
                        try:
                            import usb.util
                            usb.util.release_interface(old_sm.hardware.dev, 0)
                            usb.util.dispose_resources(old_sm.hardware.dev)
                            print("USB interface released")
                        except:
                            pass
                    old_sm.hardware = None
                print("Old state machine connection closed explicitly")
            except:
                pass

def test_pure_state_machine_recovery():
    """Test pure state machine recovery from error state with new connection."""
    print("\n" + "=" * 60)
    print("STEP 2: TESTING PURE STATE MACHINE RECOVERY")
    print("=" * 60)
    
    print("Creating new pure state machine connection...")
    try:
        # Create new pure state machine with fresh connection
        pure_sm = NimbiePureStateMachine(target_drive="1", log_level=logging.INFO)
        
        # Check hardware state before initialization
        hw_state = pure_sm.hardware.get_state()
        print(f"Hardware state before initialization: {hw_state}")
        
        if not hw_state["tray_out"]:
            print("❌ Tray is not open - error state was not preserved")
            return False
        
        print("✅ Error state preserved: Tray is still open")
        
        # Test initialization sequence - this should handle the open tray
        print("\nTesting initialization sequence...")
        print("The pure state machine should detect and handle the open tray")
        
        # Initialize - this should recover from the error state
        success = pure_sm.initialize()
        
        if success:
            print("✅ Initialization completed successfully")
            
            # Verify recovery
            hw_state = pure_sm.hardware.get_state()
            print(f"Hardware state after initialization: {hw_state}")
            
            if not hw_state["tray_out"] and not hw_state["disk_lifted"]:
                print("✅ Recovery successful: Hardware is in clean state")
                print(f"Pure state machine state: {pure_sm.state}")
                return True
            else:
                print("❌ Recovery incomplete: Hardware not fully clean")
                return False
        else:
            print("❌ Initialization failed")
            return False
            
    except Exception as e:
        print(f"❌ Pure state machine recovery failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("TRAY OPEN RECOVERY TEST")
    print("=" * 80)
    print("Testing recovery from tray open error state using separate connections")
    print("1. Create error state using old system")
    print("2. Close connection completely")
    print("3. Start pure state machine with new connection")
    print("4. Verify recovery during initialization")
    
    # Step 1: Create error state and close connection
    error_created = create_error_state()
    if not error_created:
        print("\n❌ FAILED: Could not create error state")
        return False
    
    # Brief pause to ensure connection is fully closed
    print("\nWaiting for connection to close completely...")
    time.sleep(5)
    
    # Step 2: Test pure state machine recovery with new connection
    recovery_success = test_pure_state_machine_recovery()
    
    # Summary
    print("\n" + "=" * 80)
    print("TRAY OPEN RECOVERY TEST SUMMARY")
    print("=" * 80)
    
    if recovery_success:
        print("✅ SUCCESS: Pure state machine successfully recovered from tray open error state")
        print("✅ The initialization sequence properly handles open tray during startup")
        return True
    else:
        print("❌ FAILED: Pure state machine could not recover from tray open error state")
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