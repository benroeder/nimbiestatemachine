#!/usr/bin/env python3
"""
Example of using the NimbiePureStateMachine for disk processing.

This demonstrates the pure state machine pattern where all hardware
operations happen within state transitions.
"""

import logging
import time
from nimbie import NimbiePureStateMachine


def main():
    """Main example function."""
    print("=" * 60)
    print("NIMBIE PURE STATE MACHINE EXAMPLE")
    print("=" * 60)
    
    # Initialize the pure state machine
    # macOS: Use drive index from 'drutil list' (e.g., "1", "2")
    # Linux: Use device path (e.g., "/dev/sr0", "/dev/cdrom")
    sm = NimbiePureStateMachine(
        target_drive="1",
        poll_interval=0.1,  # Poll every 100ms
        default_timeout=30.0,  # 30 second timeout for disk operations
        log_level=logging.INFO
    )
    
    try:
        # Initialize the hardware
        # This will:
        # - Check for stuck disks and clear them
        # - Ensure tray is closed and empty
        # - Put hardware in ready state
        print("\nInitializing hardware...")
        if not sm.initialize():
            print("ERROR: Failed to initialize hardware")
            return
        
        print(f"Hardware initialized! Current state: {sm.state}")
        
        # Check if we can load a disk
        if not sm.can_load_disk():
            print("\nNo disk available in queue")
            return
        
        # Load a disk using the event-driven API
        print("\nLoading disk...")
        start_time = time.time()
        
        if sm.load_next_disk():
            load_time = time.time() - start_time
            print(f"Disk loaded successfully in {load_time:.1f} seconds")
            print(f"Current state: {sm.state}")
            
            # Simulate disk processing
            print("\nProcessing disk...")
            time.sleep(2)  # Simulate work
            
            # Decide whether to accept or reject
            # In a real application, this would be based on your processing results
            disk_is_good = True  # Change to False to test reject path
            
            if disk_is_good:
                print("\nAccepting disk...")
                if sm.accept_current_disk():
                    print("Disk accepted successfully!")
                else:
                    print("ERROR: Failed to accept disk")
            else:
                print("\nRejecting disk...")
                if sm.reject_current_disk():
                    print("Disk rejected successfully!")
                else:
                    print("ERROR: Failed to reject disk")
            
            print(f"\nFinal state: {sm.state}")
            
        else:
            print("ERROR: Failed to load disk")
        
        # Demonstrate state queries
        print("\n" + "-" * 40)
        print("STATE QUERIES:")
        print(f"Is ready: {sm.is_ready()}")
        print(f"Is processing: {sm.is_processing()}")
        print(f"Can load disk: {sm.can_load_disk()}")
        
        # Demonstrate batch processing
        print("\n" + "-" * 40)
        print("BATCH PROCESSING EXAMPLE:")
        
        processed_count = 0
        accepted_count = 0
        rejected_count = 0
        
        # Process up to 5 disks (or until no more available)
        for i in range(5):
            if not sm.can_load_disk():
                print(f"\nNo more disks available (processed {processed_count})")
                break
            
            print(f"\nProcessing disk #{i+1}...")
            if sm.load_next_disk():
                # Simulate processing - alternating accept/reject
                time.sleep(1)
                
                if i % 2 == 0:
                    if sm.accept_current_disk():
                        accepted_count += 1
                        print(f"  Disk #{i+1} accepted")
                else:
                    if sm.reject_current_disk():
                        rejected_count += 1
                        print(f"  Disk #{i+1} rejected")
                
                processed_count += 1
            else:
                print(f"  ERROR: Failed to load disk #{i+1}")
                break
        
        print("\n" + "-" * 40)
        print("BATCH PROCESSING SUMMARY:")
        print(f"Total processed: {processed_count}")
        print(f"Accepted: {accepted_count}")
        print(f"Rejected: {rejected_count}")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Always clean up resources
        print("\nCleaning up...")
        sm.close()
        print("Done!")


if __name__ == "__main__":
    main()