#!/usr/bin/env python3
"""
Example script showing how to use the Nimbie State Machine for disk processing.

This example demonstrates:
- Basic disk processing with accept/reject logic
- Error handling and recovery
- Progress tracking
- Manual mode for testing
"""

import hashlib
import random
import time

from nimbie import NimbieStateMachine


def verify_disk_content():
    """
    Simulate disk content verification.
    In a real application, this would read the disk and verify its contents.
    """
    print("    Reading disk content...")
    time.sleep(3)  # Simulate time to read disk

    # Simulate verification with 80% success rate
    is_valid = random.random() < 0.8

    if is_valid:
        print("    Disk verification: PASSED")
    else:
        print("    Disk verification: FAILED")

    return is_valid


def calculate_disk_checksum():
    """
    Example of a more complex disk processing function.
    In reality, this would read actual disk data.
    """
    print("    Calculating disk checksum...")
    time.sleep(2)

    # Simulate checksum calculation
    fake_data = f"disk_data_{time.time()}".encode()
    checksum = hashlib.md5(fake_data).hexdigest()
    print(f"    Checksum: {checksum}")

    # Simulate checking against expected checksum
    # 90% success rate
    return random.random() < 0.9


def main():
    """Main example demonstrating state machine usage."""
    print("Nimbie State Machine Example")
    print("=" * 50)

    # Initialize the state machine
    print("\nInitializing Nimbie State Machine...")
    try:
        sm = NimbieStateMachine(target_drive="1")
        print("State machine initialized successfully!")
    except Exception as e:
        print(f"Failed to initialize: {e}")
        print("Make sure the Nimbie is connected and powered on.")
        return

    # Check hardware state
    print("\nChecking hardware state...")
    hw_state = sm.get_hardware_state()
    print(f"  Disks available: {'Yes' if hw_state['disk_available'] else 'No'}")
    print(f"  Tray status: {'Open' if hw_state['tray_out'] else 'Closed'}")
    print(f"  Current state: {sm.state}")

    # Example 1: Process a single disk
    print("\n" + "=" * 50)
    print("Example 1: Processing a single disk")
    print("=" * 50)

    if hw_state["disk_available"]:
        processed, accepted = sm.process_one_disk(process_fn=verify_disk_content)
        print(f"\nResult: Processed={processed}, Accepted={accepted}")
    else:
        print("No disks available. Please add disks to the input queue.")

    # Example 2: Process multiple disks with progress tracking
    print("\n" + "=" * 50)
    print("Example 2: Batch processing with progress tracking")
    print("=" * 50)

    # Check if we have disks
    hw_state = sm.get_hardware_state()
    if hw_state["disk_available"]:
        print("\nProcessing up to 5 disks...")

        # Track progress
        processed_count = 0

        def process_with_progress():
            nonlocal processed_count
            processed_count += 1
            print(f"\n  Processing disk #{processed_count}")
            return calculate_disk_checksum()

        # Process batch
        stats = sm.process_batch(count=5, process_fn=process_with_progress)

        print("\nBatch processing complete!")
        print(f"  Total processed: {stats['total']}")
        print(f"  Accepted: {stats['accepted']}")
        print(f"  Rejected: {stats['rejected']}")
        print(f"  Success rate: {stats['accepted']/stats['total']*100:.1f}%")
    else:
        print("No more disks available.")

    # Example 3: Manual mode for testing/recovery
    print("\n" + "=" * 50)
    print("Example 3: Manual mode for testing/recovery")
    print("=" * 50)

    print("\nUsing manual mode to check hardware...")
    with sm.manual_operation():
        # Open and close tray
        print("  Testing tray operation...")
        sm.manual_open_tray()
        time.sleep(1)
        sm.manual_close_tray()
        print("  Tray test complete")

        # If disk available, test placement
        if sm.get_hardware_state()["disk_available"]:
            print("  Testing disk placement...")
            sm.manual_open_tray()
            sm.manual_place_disk()
            print("  Disk placed on tray")

            # Clean up
            sm.manual_lift_disk()
            sm.manual_close_tray()
            sm.manual_accept_disk()
            print("  Test cleanup complete")

    # Example 4: Error recovery
    print("\n" + "=" * 50)
    print("Example 4: Error recovery demonstration")
    print("=" * 50)

    print("\nChecking if recovery is needed...")
    hw_state = sm.get_hardware_state()

    if hw_state["tray_out"] or hw_state["disk_lifted"]:
        print("Hardware in non-standard state. Recovering...")

        with sm.manual_operation():
            # Handle lifted disk
            if hw_state["disk_lifted"]:
                print("  Disk is lifted, dropping it...")
                if hw_state["tray_out"]:
                    sm.manual_close_tray()
                sm.manual_accept_disk()

            # Ensure tray is closed
            if sm.get_hardware_state()["tray_out"]:
                print("  Closing tray...")
                sm.manual_close_tray()

            # Reset state
            sm.manual_set_state("idle")
            print("  Recovery complete!")
    else:
        print("Hardware is in safe state. No recovery needed.")

    # Final status
    print("\n" + "=" * 50)
    print("Final Status")
    print("=" * 50)
    final_state = sm.get_hardware_state()
    print(f"  State machine: {sm.state}")
    print(f"  Tray: {'Open' if final_state['tray_out'] else 'Closed'}")
    print(f"  Disks remaining: {'Yes' if final_state['disk_available'] else 'No'}")
    print("\nExample complete!")


def continuous_processing_example():
    """
    Example of continuous disk processing.
    This would be used in a production environment.
    """
    print("Continuous Disk Processing Example")
    print("=" * 50)
    print("Press Ctrl+C to stop\n")

    sm = NimbieStateMachine(target_drive="1")
    total_processed = 0
    total_accepted = 0

    def process_disk():
        # Your actual disk processing logic here
        time.sleep(5)  # Simulate processing
        return True  # Accept all disks in this example

    try:
        while True:
            # Check for available disks
            if sm.get_hardware_state()["disk_available"]:
                print(f"\nProcessing disk #{total_processed + 1}...")
                processed, accepted = sm.process_one_disk(process_fn=process_disk)

                if processed:
                    total_processed += 1
                    if accepted:
                        total_accepted += 1

                    print(
                        f"Total processed: {total_processed}, "
                        f"Accepted: {total_accepted}, "
                        f"Rejected: {total_processed - total_accepted}"
                    )
            else:
                print(".", end="", flush=True)  # Waiting indicator
                time.sleep(5)  # Wait before checking again

    except KeyboardInterrupt:
        print(f"\n\nStopping... Final count: {total_processed} disks processed")

        # Ensure hardware is in safe state
        with sm.manual_operation():
            if sm.get_hardware_state()["tray_out"]:
                sm.manual_close_tray()


if __name__ == "__main__":
    # Run the main example
    main()

    # Uncomment to run continuous processing example
    # continuous_processing_example()
