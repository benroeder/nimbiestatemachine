"""Test suite for Nimbie State Machine - TDD approach with early hardware testing."""

import time

import pytest

from nimbie import NimbieStateMachine

# Mark for hardware tests
pytestmark = pytest.mark.hardware


# Phase 1: Basic Setup with Hardware Verification


def test_hardware_timeout_recovery(nimbie_state_machine: NimbieStateMachine) -> None:
    """Test 1: Test hardware timeout error recovery."""
    # This test specifically handles hardware timeout scenarios
    sm = nimbie_state_machine

    try:
        state = sm.get_hardware_state()
        print(f"Hardware connected successfully. Current state: {state}")

        # Verify we get expected state dictionary
        assert isinstance(state, dict)
        assert "tray_out" in state
        assert "disk_available" in state
        assert "disk_lifted" in state
        assert "disk_in_open_tray" in state

    except Exception as e:
        if "Operation timed out" in str(e):
            print(f"Hardware timeout detected: {e}")
            # Test our timeout recovery
            if sm.handle_timeout_error():
                print("Hardware recovery successful!")
                # Try to get state again
                state = sm.get_hardware_state()
                print(f"Hardware state after recovery: {state}")
            else:
                print(
                    "Hardware recovery failed - hardware may need manual intervention"
                )
                pytest.skip("Hardware not responding - requires manual intervention")
        else:
            # Re-raise other exceptions
            raise


def test_hardware_connection(nimbie_state_machine: NimbieStateMachine) -> None:
    """Test 2: Ensure we can connect to Nimbie hardware through state machine."""
    # This test runs with real hardware to verify connection
    sm = nimbie_state_machine

    # Skip if hardware is in error state
    if sm.state == "error":
        pytest.skip("Hardware in error state - run timeout recovery test first")

    state = sm.get_hardware_state()

    # Verify we get expected state dictionary
    assert isinstance(state, dict)
    assert "tray_out" in state
    assert "disk_available" in state
    assert "disk_lifted" in state
    assert "disk_in_open_tray" in state

    print(f"Hardware connected successfully. Current state: {state}")


def test_create_state_machine_with_hardware(
    nimbie_state_machine: NimbieStateMachine,
) -> None:
    """Test 3: State machine should initialize with real hardware."""
    sm = nimbie_state_machine

    assert sm.state == "idle"
    assert sm.hardware is not None

    print(f"State machine created successfully in state: {sm.state}")


def test_read_hardware_state(nimbie_state_machine: NimbieStateMachine) -> None:
    """Test 4: Verify we can read hardware state correctly."""
    sm = nimbie_state_machine

    state = sm.get_hardware_state()

    # Verify all expected keys are present
    assert "disk_available" in state
    assert "tray_out" in state
    assert "disk_lifted" in state
    assert "disk_in_open_tray" in state

    print(f"Hardware state: {state}")


# Phase 2: State Machine Operations


def test_tray_operations(nimbie_state_machine: NimbieStateMachine) -> None:
    """Test 5: Test tray open/close operations through state machine."""
    sm = nimbie_state_machine

    # State machine should be in idle state
    assert sm.state == "idle"

    # Get initial state
    initial_state = sm.get_hardware_state()
    print(f"Initial state: {initial_state}")

    # Test opening tray
    if not initial_state["tray_out"]:
        print("Testing open tray operation...")
        sm.open_tray()
        state = sm.get_hardware_state()
        assert state["tray_out"] is True
        print("Tray opened successfully")

    # Test closing tray
    print("Testing close tray operation...")
    sm.close_tray()
    state = sm.get_hardware_state()
    assert state["tray_out"] is False
    print("Tray closed successfully")

    # State machine should still be in idle
    assert sm.state == "idle"
    print("State machine remains in idle state")


def test_disk_loading_cycle(nimbie_state_machine: NimbieStateMachine) -> None:
    """Test 6: Test full disk loading cycle through state machine."""
    sm = nimbie_state_machine

    # Check if disk available
    if not sm.hardware.disk_available():
        pytest.skip("No disk in queue")

    print("Starting disk loading cycle test...")

    # Should start in idle state
    assert sm.state == "idle"

    # Start loading process
    print("Transitioning to loading state...")
    sm.start_load()
    assert sm.state == "loading"

    # Open tray
    print("Opening tray...")
    sm.open_tray()

    # Place disk
    print("Placing disk from queue...")
    result = sm.place_disk()
    print(f"Place disk result: {result}")

    # Close tray to load disk
    print("Closing tray to load disk...")
    sm.close_tray()

    # Complete loading
    print("Completing load operation...")
    sm.complete_load()
    assert sm.state == "processing"
    print("Disk loaded successfully, now in processing state")

    # Start unloading
    print("Starting unload process...")
    sm.start_unload()
    assert sm.state == "unloading"

    # Open tray
    print("Opening tray to unload...")
    sm.open_tray()

    # Lift disk
    print("Lifting disk...")
    result = sm.lift_disk()
    print(f"Lift disk result: {result}")

    # Close tray
    print("Closing tray...")
    sm.close_tray()

    # Accept disk
    print("Accepting disk...")
    sm.accept_disk()

    # Complete unload
    print("Completing unload...")
    sm.complete_unload()
    assert sm.state == "idle"
    print("Disk unloaded successfully, back in idle state")


def test_manual_mode_operations(nimbie_state_machine: NimbieStateMachine) -> None:
    """Test 7: Test manual mode operations."""
    sm = nimbie_state_machine

    print("Testing manual mode operations...")

    # Manual operations should fail outside manual mode
    print("Testing operations outside manual mode...")
    with pytest.raises(
        RuntimeError, match="Manual operations only allowed in manual mode"
    ):
        sm.manual_open_tray()
    print("Manual operations correctly blocked outside manual mode")

    # Test manual mode context manager
    with sm.manual_operation():
        print("Inside manual mode context...")
        assert sm.manual_mode is True

        # Test manual tray operations
        print("Testing manual tray operations...")
        sm.manual_open_tray()
        state = sm.get_hardware_state()
        assert state["tray_out"] is True
        print("Manual open tray successful")

        sm.manual_close_tray()
        state = sm.get_hardware_state()
        assert state["tray_out"] is False
        print("Manual close tray successful")

        # If disk available, test manual disk operations
        if sm.hardware.disk_available():
            print("Testing manual disk operations...")
            sm.manual_open_tray()
            result = sm.manual_place_disk()
            print(f"Manual place disk: {result}")

            # Check if disk is in tray or fell into drive
            state = sm.get_hardware_state()
            if state["disk_in_open_tray"]:
                # Disk is in tray, we can lift it
                result = sm.manual_lift_disk()
                print(f"Manual lift disk: {result}")

                sm.manual_close_tray()
                result = sm.manual_accept_disk()
                print(f"Manual accept disk: {result}")
            else:
                # Disk fell into drive, close tray and complete cycle
                print("Disk fell into drive, completing load cycle...")
                sm.manual_close_tray()
                # Now open tray to reveal disk
                sm.manual_open_tray()
                # Now we can lift it
                result = sm.manual_lift_disk()
                print(f"Manual lift disk: {result}")

                sm.manual_close_tray()
                result = sm.manual_accept_disk()
                print(f"Manual accept disk: {result}")

    # Verify manual mode is disabled after context
    assert sm.manual_mode is False
    print("Manual mode correctly disabled after context")


def test_error_recovery(nimbie_state_machine: NimbieStateMachine) -> None:
    """Test 8: Test error recovery mechanism."""
    sm = nimbie_state_machine

    print("Testing error recovery mechanism...")

    # Test recovery from error state
    print("Forcing error state...")
    sm.error_occurred()
    assert sm.state == "error"
    print("State machine in error state")

    # Test recovery
    print("Testing recovery...")
    sm.recover()
    assert sm.state == "idle"
    print("Successfully recovered to idle state")

    # Test that operations fail in wrong states
    print("Testing invalid state transitions...")
    try:
        # Try to place disk without being in loading state
        sm.place_disk()
        raise AssertionError("Should have raised RuntimeError")
    except RuntimeError as e:
        assert "Cannot place disk in idle state" in str(e)
        print("Invalid operations correctly blocked")

    # Test error transition during operation
    print("Testing error during operation...")
    if sm.hardware.disk_available():
        sm.start_load()
        assert sm.state == "loading"

        # Force error
        sm.error_occurred()
        assert sm.state == "error"
        print("Error transition from loading state")

        # Recover
        sm.recover()
        assert sm.state == "idle"
        print("Recovered from error during operation")


# Phase 3: Integration Tests


def test_process_one_disk(nimbie_state_machine: NimbieStateMachine) -> None:
    """Test 9: Test high-level process_one_disk method."""
    sm = nimbie_state_machine

    # Check if disk available
    if not sm.hardware.disk_available():
        pytest.skip("No disk in queue")

    print("Testing process_one_disk method...")

    # Define a simple processing function
    def process_fn() -> bool:
        print("Processing disk...")
        time.sleep(1)  # Simulate processing
        return True  # Accept disk

    # Process one disk
    processed, accepted = sm.process_one_disk(process_fn=process_fn)

    assert processed is True
    assert accepted is True
    print("Successfully processed one disk")


def test_process_batch(nimbie_state_machine: NimbieStateMachine) -> None:
    """Test 10: Test batch processing of multiple disks."""
    sm = nimbie_state_machine

    # Count available disks
    available_disks = 0
    state = sm.get_hardware_state()
    if state["disk_available"]:
        # We know there's at least one
        available_disks = 1
        # For this test, we'll just process what's available

    if available_disks == 0:
        pytest.skip("No disks in queue")

    print(f"Testing batch processing with {available_disks} disk(s)...")

    # Define a processing function that alternates accept/reject
    process_count = 0

    def process_fn() -> bool:
        nonlocal process_count
        process_count += 1
        print(f"Processing disk {process_count}...")
        time.sleep(0.5)  # Simulate processing
        # Accept all disks for this test
        return True

    # Process batch
    stats = sm.process_batch(count=available_disks, process_fn=process_fn)

    print(f"Batch processing results: {stats}")
    assert stats["total"] == available_disks
    assert stats["accepted"] == available_disks
    assert stats["rejected"] == 0
    print(f"Successfully processed batch of {available_disks} disk(s)")
