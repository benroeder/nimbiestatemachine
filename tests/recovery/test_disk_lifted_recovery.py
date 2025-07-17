#!/usr/bin/env python3
"""Test disk lifted recovery with separate connections."""

import logging
import time
import sys
from nimbie import NimbieStateMachine
from nimbie.pure_state_machine import NimbiePureStateMachine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def create_error_state():
    """Create disk lifted error state using old system, then close connection."""
    print("=" * 60)
    print("STEP 1: CREATING ERROR STATE (Disk Lifted)")
    print("=" * 60)
    
    print("Using old state machine to create disk lifted error state...")
    old_sm = None
    try:
        # Create old state machine connection
        old_sm = NimbieStateMachine("1", log_level=logging.INFO)
        
        # Check if we have a disk available
        hw_state = old_sm.get_hardware_state()
        print(f"Initial hardware state: {hw_state}")
        
        if not hw_state["disk_available"]:
            print("❌ No disk available - cannot create disk lifted error state")
            return False
        
        # Use manual operations to create error state
        with old_sm.manual_operation():
            # Create error state: disk lifted with tray closed
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
            
            # Verify error state created
            hw_state = old_sm.get_hardware_state()
            print(f"Hardware state after error creation: {hw_state}")
            
            if hw_state["disk_lifted"] and not hw_state["tray_out"]:
                print("✅ Error state created successfully: Disk lifted with tray closed")
                return True
            else:
                print("❌ Failed to create disk lifted error state")
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
        
        if not hw_state["disk_lifted"]:
            print("❌ Disk is not lifted - error state was not preserved")
            return False
        
        print("✅ Error state preserved: Disk is lifted")
        
        # Test initialization sequence - this should handle the lifted disk
        print("\nTesting initialization sequence...")
        print("The pure state machine should detect and handle the lifted disk")
        
        # Initialize - this should recover from the error state
        success = pure_sm.initialize()
        
        if success:
            print("✅ Initialization completed successfully")
            
            # Verify recovery
            hw_state = pure_sm.hardware.get_state()
            print(f"Hardware state after initialization: {hw_state}")
            
            if not hw_state["disk_lifted"] and not hw_state["tray_out"]:
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
    print("DISK LIFTED RECOVERY TEST")
    print("=" * 80)
    print("Testing recovery from disk lifted error state using separate connections")
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
    print("DISK LIFTED RECOVERY TEST SUMMARY")
    print("=" * 80)
    
    if recovery_success:
        print("✅ SUCCESS: Pure state machine successfully recovered from disk lifted error state")
        print("✅ The initialization sequence properly handles lifted disk during startup")
        return True
    else:
        print("❌ FAILED: Pure state machine could not recover from disk lifted error state")
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