#!/usr/bin/env python3
"""Test cycling through disk queue with progress display."""

import time

from nimbie import NimbieStateMachine


def process_disk():
    """Simulate disk processing."""
    print("    Processing disk...")
    time.sleep(2)  # Simulate processing time
    return True  # Accept all disks


def main():
    print("Nimbie Queue Processing Test")
    print("=" * 50)

    try:
        # Initialize with drive 1 (Nimbie drive)
        sm = NimbieStateMachine(target_drive="1")
        print("Nimbie initialized on drive 1")

        # Check initial state
        state = sm.get_hardware_state()
        print("\nInitial state:")
        print(f"   - Disks available: {state['disk_available']}")
        print(f"   - Tray position: {'Open' if state['tray_out'] else 'Closed'}")
        print(f"   - Current state: {sm.state}")

        if not state["disk_available"]:
            print("\nNo disks in queue! Please add disks to the input queue.")
            return

        # Process a batch of disks
        print("\nProcessing batch of 3 disks...\n")

        try:
            stats = sm.process_batch(count=3, process_fn=process_disk)

            print("\nBatch processing complete!")
            print(f"   - Total processed: {stats['total']}")
            print(f"   - Accepted: {stats['accepted']}")
            print(f"   - Rejected: {stats['rejected']}")

        except KeyboardInterrupt:
            print("\n\nProcessing interrupted by user")
            sm.stop_continuous()

        # Final state
        final_state = sm.get_hardware_state()
        print("\nFinal state:")
        print(f"   - Disks remaining: {final_state['disk_available']}")
        print(f"   - State machine: {sm.state}")

    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()
