#!/usr/bin/env python3
"""
Example: Automated Disk Imaging with Nimbie State Machine

This example shows how to use the Nimbie for automated disk imaging,
such as backing up a collection of CDs/DVDs or creating ISO images.
"""

import datetime
import subprocess
import time
from contextlib import suppress
from pathlib import Path

from nimbie import NimbieStateMachine


class DiskImager:
    """Handles disk imaging operations."""

    def __init__(self, output_dir="disk_images"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.processed_count = 0
        self.success_count = 0
        self.failed_disks = []

    def get_disk_info(self):
        """Get information about the currently mounted disk."""
        try:
            # On macOS, use diskutil
            result = subprocess.run(
                ["diskutil", "info", "/dev/disk2"],  # Adjust device as needed
                capture_output=True,
                text=True,
            )

            # Parse disk label/name
            for line in result.stdout.split("\n"):
                if "Volume Name:" in line:
                    name = line.split("Volume Name:")[1].strip()
                    if name and name != "(null)":
                        return name

            return f"disk_{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')}"

        except Exception as e:
            print(f"    Could not get disk info: {e}")
            return f"disk_{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    def create_iso_image(self, disk_name):
        """Create an ISO image of the current disk."""
        output_file = self.output_dir / f"{disk_name}.iso"

        # Prevent overwriting existing files
        if output_file.exists():
            timestamp = datetime.datetime.now(datetime.timezone.utc).strftime(
                "%Y%m%d_%H%M%S"
            )
            output_file = self.output_dir / f"{disk_name}_{timestamp}.iso"

        print(f"    Creating ISO image: {output_file.name}")

        try:
            # On macOS, use hdiutil
            # Adjust the device path as needed for your system
            subprocess.run(
                [
                    "hdiutil",
                    "create",
                    "-srcdevice",
                    "/dev/disk2",
                    "-format",
                    "UDTO",
                    "-o",
                    str(output_file),
                ],
                check=True,
                capture_output=True,
            )

            # Rename .cdr to .iso
            cdr_file = output_file.with_suffix(".cdr")
            if cdr_file.exists():
                cdr_file.rename(output_file)

            print(f"    ISO created successfully: {output_file.name}")
            return True

        except subprocess.CalledProcessError as e:
            print(f"    Failed to create ISO: {e}")
            return False

    def process_disk(self):
        """Process a single disk - main callback for state machine."""
        self.processed_count += 1
        print(f"\n  Disk #{self.processed_count} inserted")

        # Wait for disk to mount
        print("    Waiting for disk to mount...")
        time.sleep(5)

        # Get disk information
        disk_name = self.get_disk_info()
        print(f"    Disk name: {disk_name}")

        # Create ISO image
        success = self.create_iso_image(disk_name)

        if success:
            self.success_count += 1
            print("    Result: SUCCESS")

            # Log successful backup
            with (self.output_dir / "backup_log.txt").open("a") as f:
                f.write(
                    f"{datetime.datetime.now(datetime.timezone.utc)}: {disk_name} - SUCCESS\n"
                )
        else:
            self.failed_disks.append(disk_name)
            print("    Result: FAILED")

            # Log failed backup
            with (self.output_dir / "backup_log.txt").open("a") as f:
                f.write(
                    f"{datetime.datetime.now(datetime.timezone.utc)}: {disk_name} - FAILED\n"
                )

        # Eject disk before returning
        with suppress(Exception):
            subprocess.run(["drutil", "eject"], check=True)

        return success  # True = accept, False = reject

    def print_summary(self):
        """Print summary of imaging session."""
        print("\n" + "=" * 50)
        print("Disk Imaging Summary")
        print("=" * 50)
        print(f"Total disks processed: {self.processed_count}")
        print(f"Successful: {self.success_count}")
        print(f"Failed: {len(self.failed_disks)}")

        if self.failed_disks:
            print("\nFailed disks:")
            for disk in self.failed_disks:
                print(f"  - {disk}")

        print(f"\nImages saved to: {self.output_dir.absolute()}")


def main():
    """Main disk imaging workflow."""
    print("Nimbie Automated Disk Imaging")
    print("=" * 50)

    # Initialize components
    print("\nInitializing...")
    try:
        sm = NimbieStateMachine(target_drive="1")
        imager = DiskImager()
        print("Ready to process disks!")
    except Exception as e:
        print(f"Initialization failed: {e}")
        return

    # Check initial state
    hw_state = sm.get_hardware_state()
    if not hw_state["disk_available"]:
        print("\nNo disks in input queue. Please load disks and restart.")
        return

    print("\nDisks detected in input queue.")
    print("Starting automated imaging process...")
    print("(Press Ctrl+C to stop after current disk)\n")

    try:
        # Process all available disks
        sm.process_batch(process_fn=imager.process_disk)

    except KeyboardInterrupt:
        print("\n\nStopping after current disk...")

    finally:
        # Print summary
        imager.print_summary()

        # Ensure hardware is in safe state
        print("\nReturning hardware to safe state...")
        with sm.manual_operation():
            hw_state = sm.get_hardware_state()

            # Handle any lifted disk
            if hw_state["disk_lifted"]:
                if hw_state["tray_out"]:
                    sm.manual_close_tray()
                sm.manual_accept_disk()

            # Close tray if open
            if sm.get_hardware_state()["tray_out"]:
                sm.manual_close_tray()

        print("Done!")


def verify_mode_example():
    """
    Example of using Nimbie to verify existing disk images.
    Compares physical disks against previously created ISOs.
    """
    print("Disk Verification Mode")
    print("=" * 50)

    sm = NimbieStateMachine(target_drive="1")
    verified_count = 0
    mismatch_count = 0

    def verify_disk():
        nonlocal verified_count, mismatch_count

        # Wait for mount
        time.sleep(5)

        # In real implementation:
        # 1. Mount the disk
        # 2. Calculate checksum of disk contents
        # 3. Compare with stored ISO checksum
        # 4. Return True if match, False if mismatch

        # Simulate verification
        print("    Calculating disk checksum...")
        time.sleep(3)

        # Simulate 95% match rate
        import random

        matches = random.random() < 0.95

        if matches:
            print("    Verification: PASSED")
            verified_count += 1
        else:
            print("    Verification: FAILED - Checksum mismatch")
            mismatch_count += 1

        # Eject disk
        with suppress(Exception):
            subprocess.run(["drutil", "eject"], check=True)

        return matches

    print("\nPlace disks to verify in the input queue.")
    print("Matching disks go to accept pile, mismatches to reject pile.\n")

    stats = sm.process_batch(process_fn=verify_disk)

    print("\nVerification complete!")
    print(f"Total checked: {stats['total']}")
    print(f"Matches: {verified_count}")
    print(f"Mismatches: {mismatch_count}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--verify":
        verify_mode_example()
    else:
        main()
