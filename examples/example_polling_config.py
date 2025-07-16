#!/usr/bin/env python3
"""
Example: Configure polling intervals and timeouts.

This example demonstrates how to configure the polling behavior
of the state machine for different use cases.
"""

import time

from nimbie import NimbieStateMachine


def main():
    print("=== Polling Configuration Example ===\n")

    # Example 1: Fast polling for responsive operation
    print("1. Fast polling configuration (responsive but higher CPU)")
    sm_fast = NimbieStateMachine(poll_interval=0.05, default_timeout=5.0)
    print(f"   Poll interval: {sm_fast.poll_interval}s")
    print(f"   Default timeout: {sm_fast.default_timeout}s")
    print("   Good for: Interactive applications, testing\n")

    # Example 2: Slow polling for batch operations
    print("2. Slow polling configuration (lower CPU, less responsive)")
    sm_slow = NimbieStateMachine(poll_interval=0.5, default_timeout=30.0)
    print(f"   Poll interval: {sm_slow.poll_interval}s")
    print(f"   Default timeout: {sm_slow.default_timeout}s")
    print("   Good for: Overnight batch processing\n")

    # Example 3: Custom timeouts for specific operations
    print("3. Using custom timeouts for specific operations")
    sm = NimbieStateMachine(target_drive="1")  # Default settings

    # Check hardware state
    state = sm.get_hardware_state()
    print("\nCurrent hardware state:")
    print(f"   Tray out: {state['tray_out']}")
    print(f"   Disk available: {state['disk_available']}")

    if state["tray_out"]:
        print("\n   Closing tray with default timeout...")
        sm.close_tray()
    else:
        print("\n   Opening tray with custom timeout...")
        # Some operations can use custom timeouts
        if sm.wait_for_tray_open(timeout=3.0):
            print("   Tray opened within 3 seconds")
        else:
            print("   Tray did not open within 3 seconds")

    # Example 4: Demonstrating polling in action
    print("\n4. Demonstrating polling behavior")
    print("   Watch the state machine poll for disk availability...")

    # This will poll every poll_interval seconds
    print(f"   Checking for disk (polling every {sm.poll_interval}s)...")
    start_time = time.time()
    timeout = 3.0

    while time.time() - start_time < timeout:
        if sm.hardware.disk_available():
            print(f"   Disk detected after {time.time() - start_time:.1f}s")
            break
        print(f"   · No disk at {time.time() - start_time:.1f}s")
        time.sleep(sm.poll_interval)
    else:
        print(f"   No disk found after {timeout}s")

    # Example 5: Error handling with timeouts
    print("\n5. Timeout error handling")
    print("   Attempting to wait for a disk that won't appear...")

    # This will timeout
    result = sm.wait_for_disk_placed(timeout=2.0)
    if result:
        print("   Disk was placed")
    else:
        print("   Operation timed out after 2.0s (as expected)")

    print("\n=== Configuration Guidelines ===")
    print("• Fast polling (0.05s): Use for interactive/testing")
    print("• Normal polling (0.1s): Default, good balance")
    print("• Slow polling (0.5s+): Use for batch operations")
    print("• Timeout = 2-3x expected operation time")
    print("• Tray operations: ~2-3s typical")
    print("• Disk placement: ~10-15s typical")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
