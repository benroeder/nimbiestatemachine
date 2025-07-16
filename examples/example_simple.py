#!/usr/bin/env python3
"""
Simple example: Process all disks in the queue.

This is the simplest possible example - it processes all available disks
and accepts them all.
"""

import time

from nimbie import NimbieStateMachine


def main():
    # Create state machine
    sm = NimbieStateMachine(target_drive="1")

    # Check if disks are available
    if not sm.get_hardware_state()["disk_available"]:
        print("No disks available. Please add disks to the input queue.")
        return

    # Process all disks
    print("Processing all available disks...")

    def process_disk():
        """Simple processing function that accepts all disks."""
        print("  Processing disk...")
        time.sleep(3)  # Simulate some work
        print("  Done!")
        return True  # Accept the disk

    # Process batch
    stats = sm.process_batch(process_fn=process_disk)

    # Show results
    print(f"\nComplete! Processed {stats['total']} disks.")
    print("All disks accepted and placed in the accept pile.")


if __name__ == "__main__":
    main()
