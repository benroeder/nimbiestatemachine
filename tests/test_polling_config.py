"""Phase 2.5: Test different polling configurations with real hardware."""

import time

import pytest

from nimbie import NimbieDriver, NimbieStateMachine


class TestPollingConfigurations:
    """Test different polling configurations."""

    def test_fast_polling(self, nimbie_hardware: NimbieDriver) -> None:
        """Test with fast polling (0.05s)."""
        sm = NimbieStateMachine(
            target_drive="1",
            hardware=nimbie_hardware,
            poll_interval=0.05,
            default_timeout=5.0,
        )
        assert sm.poll_interval == 0.05
        assert sm.default_timeout == 5.0

        # Test tray operation with fast polling
        state = sm.get_hardware_state()
        if state["tray_out"]:
            sm.close_tray()

        # Time tray open
        start = time.time()
        sm.open_tray()
        elapsed = time.time() - start

        # With 0.05s polling, we should see more polls
        expected_polls = int(elapsed / 0.05)
        print(
            f"\nFast polling (0.05s): Tray opened in {elapsed:.2f}s (~{expected_polls} polls)"
        )

        # Close tray
        sm.close_tray()

    def test_slow_polling(self, nimbie_hardware: NimbieDriver) -> None:
        """Test with slow polling (0.5s)."""
        sm = NimbieStateMachine(
            target_drive="1",
            hardware=nimbie_hardware,
            poll_interval=0.5,
            default_timeout=10.0,
        )
        assert sm.poll_interval == 0.5
        assert sm.default_timeout == 10.0

        # Test tray operation with slow polling
        state = sm.get_hardware_state()
        if state["tray_out"]:
            sm.close_tray()

        # Time tray open
        start = time.time()
        sm.open_tray()
        elapsed = time.time() - start

        # With 0.5s polling, we should see fewer polls
        expected_polls = int(elapsed / 0.5)
        print(
            f"\nSlow polling (0.5s): Tray opened in {elapsed:.2f}s (~{expected_polls} polls)"
        )

        # Close tray
        sm.close_tray()

    def test_timeout_scenarios(self, nimbie_hardware: NimbieDriver) -> None:
        """Test timeout handling."""
        sm = NimbieStateMachine(
            target_drive="1",
            hardware=nimbie_hardware,
            poll_interval=0.1,
            default_timeout=1.0,
        )

        # Test waiting for a state that won't happen
        print("\nTesting timeout for disk that won't appear...")
        start = time.time()
        result = sm.wait_for_disk_placed(timeout=1.0)
        elapsed = time.time() - start

        assert result is False, "Should have timed out"
        assert 0.9 < elapsed < 1.2, f"Timeout not accurate: {elapsed}s"
        print(f"Correctly timed out after {elapsed:.2f}s")

        # Test with custom timeout
        print("\nTesting with custom short timeout (0.5s)...")
        start = time.time()
        result = sm.wait_for_disk_lifted(timeout=0.5)
        elapsed = time.time() - start

        assert result is False
        # Allow more margin due to USB communication overhead
        assert 0.4 < elapsed < 0.8, f"Custom timeout not accurate: {elapsed}s"
        print(f"Correctly timed out after {elapsed:.2f}s")

    def test_polling_performance(self, nimbie_hardware: NimbieDriver) -> None:
        """Measure polling performance and suggest optimal values."""
        sm = NimbieStateMachine(target_drive="1", hardware=nimbie_hardware)

        timings = []

        # Run 3 tray cycles
        for i in range(3):
            # Ensure tray is closed
            state = sm.get_hardware_state()
            if state["tray_out"]:
                sm.close_tray()

            # Time tray open
            start = time.time()
            sm.open_tray()
            open_time = time.time() - start

            # Time tray close
            start = time.time()
            sm.close_tray()
            close_time = time.time() - start

            timings.append((open_time, close_time))
            print(f"\nCycle {i + 1}: Open={open_time:.2f}s, Close={close_time:.2f}s")

        # Calculate averages
        avg_open = sum(t[0] for t in timings) / len(timings)
        avg_close = sum(t[1] for t in timings) / len(timings)
        max_open = max(t[0] for t in timings)
        max_close = max(t[1] for t in timings)

        print(f"\nAverage times: Open={avg_open:.2f}s, Close={avg_close:.2f}s")
        print(f"Maximum times: Open={max_open:.2f}s, Close={max_close:.2f}s")

        # Verify current defaults are reasonable
        assert sm.poll_interval == 0.1, "Default poll interval should be 0.1s"
        assert sm.default_timeout == 10.0, "Default timeout should be 10.0s"

        # Check that defaults provide good safety margin
        assert sm.default_timeout > max_open * 2, (
            "Timeout should be > 2x max operation time"
        )
        assert sm.default_timeout > max_close * 2, (
            "Timeout should be > 2x max operation time"
        )

        print("\nCurrent defaults (0.1s poll, 10s timeout) are appropriate")


class TestPollingWithStateChanges:
    """Test polling detects state changes correctly."""

    def test_disk_placement_polling(self, nimbie_hardware: NimbieDriver) -> None:
        """Test that polling correctly detects disk placement."""
        sm = NimbieStateMachine(
            target_drive="1", hardware=nimbie_hardware, poll_interval=0.1
        )

        # Check if we have a disk to test with
        if not sm.hardware.disk_available():
            pytest.skip("No disk available for testing")

        # Ensure tray is open
        state = sm.get_hardware_state()
        if not state["tray_out"]:
            sm.open_tray()

        # Ensure no disk in tray
        state = sm.get_hardware_state()
        if state["disk_in_open_tray"]:
            # Remove it first using manual mode
            with sm.manual_operation():
                sm.manual_lift_disk()
                sm.manual_close_tray()
                sm.manual_accept_disk()
                sm.manual_open_tray()

        # Now place disk and verify polling works
        print("\nPlacing disk and waiting for detection...")
        sm.hardware.place_disk()  # Send command

        # Poll for disk to appear
        start = time.time()
        result = sm.wait_for_disk_placed(timeout=15.0)
        elapsed = time.time() - start

        assert result is True, "Disk should have been detected"
        print(f"Disk detected after {elapsed:.2f}s of polling")

        # Clean up - verify disk is actually there before trying to lift
        state = sm.get_hardware_state()
        if state["disk_in_open_tray"]:
            with sm.manual_operation():
                sm.manual_lift_disk()
                sm.manual_close_tray()
                sm.manual_accept_disk()
