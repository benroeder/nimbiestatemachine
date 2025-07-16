"""Test suite for polling infrastructure in the state machine."""

import time
from unittest.mock import MagicMock

import pytest

from nimbie import NimbieStateMachine


class TestPollingInfrastructure:
    """Test the base polling functionality."""

    def test_poll_interval_config(self):
        """Test that poll_interval can be configured."""
        # Test default
        sm = NimbieStateMachine(target_drive="1", hardware=MagicMock())
        assert sm.poll_interval == 0.1

        # Test custom interval
        sm = NimbieStateMachine(
            target_drive="1", hardware=MagicMock(), poll_interval=0.05
        )
        assert sm.poll_interval == 0.05

    def test_timeout_config(self):
        """Test that default_timeout can be configured."""
        # Test default
        sm = NimbieStateMachine(target_drive="1", hardware=MagicMock())
        assert sm.default_timeout == 10.0

        # Test custom timeout
        sm = NimbieStateMachine(
            target_drive="1", hardware=MagicMock(), default_timeout=5.0
        )
        assert sm.default_timeout == 5.0

    def test_poll_until_success(self):
        """Test _poll_until succeeds when condition is met."""
        sm = NimbieStateMachine(
            target_drive="1", hardware=MagicMock(), poll_interval=0.01
        )

        # Condition that succeeds immediately
        condition = MagicMock(return_value=True)
        result = sm._poll_until(condition, timeout=1.0)

        assert result is True
        condition.assert_called()

    def test_poll_until_timeout(self):
        """Test _poll_until returns False on timeout."""
        sm = NimbieStateMachine(
            target_drive="1", hardware=MagicMock(), poll_interval=0.01
        )

        # Condition that never succeeds
        condition = MagicMock(return_value=False)
        start = time.time()
        result = sm._poll_until(condition, timeout=0.1)
        elapsed = time.time() - start

        assert result is False
        assert elapsed >= 0.1  # Should have waited full timeout
        assert elapsed < 0.2  # But not much longer
        assert condition.call_count > 5  # Should have polled multiple times

    def test_poll_until_eventual_success(self):
        """Test _poll_until succeeds after several attempts."""
        sm = NimbieStateMachine(
            target_drive="1", hardware=MagicMock(), poll_interval=0.01
        )

        # Condition that succeeds after 3 calls
        call_count = 0

        def condition():
            nonlocal call_count
            call_count += 1
            return call_count >= 3

        result = sm._poll_until(condition, timeout=1.0)

        assert result is True
        assert call_count >= 3

    def test_poll_until_handles_exceptions(self):
        """Test _poll_until continues polling even if condition raises."""
        sm = NimbieStateMachine(
            target_drive="1", hardware=MagicMock(), poll_interval=0.01
        )

        # Condition that raises then succeeds
        call_count = 0

        def condition():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Test error")
            return True

        result = sm._poll_until(condition, timeout=1.0)

        assert result is True
        assert call_count >= 3

    def test_poll_until_error_logging(self):
        """Test _poll_until logs errors appropriately."""
        sm = NimbieStateMachine(
            target_drive="1", hardware=MagicMock(), poll_interval=0.01
        )

        # Mock the logger
        sm.logger.debug = MagicMock()
        sm.logger.warning = MagicMock()

        # Condition that always fails
        def condition():
            raise Exception("Test error")

        result = sm._poll_until(condition, timeout=0.05, error_msg="Testing polling")

        assert result is False
        # Should have logged debug messages for errors
        assert any(
            "Testing polling" in str(call) for call in sm.logger.debug.call_args_list
        )
        # Should have logged timeout warning
        sm.logger.warning.assert_called_with("Polling timeout: Testing polling")

    def test_poll_until_respects_interval(self):
        """Test that polling respects the configured interval."""
        sm = NimbieStateMachine(
            target_drive="1", hardware=MagicMock(), poll_interval=0.05
        )

        # Track call times
        call_times = []

        def condition():
            call_times.append(time.time())
            return False

        sm._poll_until(condition, timeout=0.2)

        # Should have at least 3 calls (0, 0.05, 0.1, 0.15)
        assert len(call_times) >= 3

        # Check intervals between calls
        for i in range(1, len(call_times)):
            interval = call_times[i] - call_times[i - 1]
            assert interval >= 0.04  # Allow some tolerance
            assert interval <= 0.06


class TestPollingWithHardware:
    """Test polling with mocked hardware operations."""

    @pytest.fixture
    def mock_hardware(self):
        """Create a mock hardware instance."""
        hardware = MagicMock()
        # Default state
        hardware.get_state.return_value = {
            "disk_available": True,
            "disk_in_open_tray": False,
            "disk_lifted": False,
            "tray_out": False,
        }
        return hardware

    def test_polling_state_changes(self, mock_hardware):
        """Test polling for hardware state changes."""
        sm = NimbieStateMachine(
            target_drive="1", hardware=mock_hardware, poll_interval=0.01
        )

        # Simulate tray opening after 3 polls
        poll_count = 0

        def get_state_side_effect():
            nonlocal poll_count
            poll_count += 1
            if poll_count < 3:
                return {
                    "tray_out": False,
                    "disk_available": True,
                    "disk_in_open_tray": False,
                    "disk_lifted": False,
                }
            return {
                "tray_out": True,
                "disk_available": True,
                "disk_in_open_tray": False,
                "disk_lifted": False,
            }

        mock_hardware.get_state.side_effect = get_state_side_effect

        # Poll for tray open
        result = sm._poll_until(
            lambda: sm.hardware.get_state()["tray_out"], timeout=1.0
        )

        assert result is True
        assert poll_count >= 3


class TestTrayPollingMethods:
    """Test tray-specific polling methods."""

    @pytest.fixture
    def mock_hardware(self):
        """Create a mock hardware instance."""
        hardware = MagicMock()
        # Default state - tray closed
        hardware.get_state.return_value = {
            "disk_available": True,
            "disk_in_open_tray": False,
            "disk_lifted": False,
            "tray_out": False,
        }
        return hardware

    def test_wait_for_tray_open_success(self, mock_hardware):
        """Test wait_for_tray_open succeeds when tray opens."""
        sm = NimbieStateMachine(
            target_drive="1", hardware=mock_hardware, poll_interval=0.01
        )

        # Simulate tray opening after 2 polls
        poll_count = 0

        def get_state_side_effect():
            nonlocal poll_count
            poll_count += 1
            return {
                "tray_out": poll_count >= 2,
                "disk_available": True,
                "disk_in_open_tray": False,
                "disk_lifted": False,
            }

        mock_hardware.get_state.side_effect = get_state_side_effect

        result = sm.wait_for_tray_open(timeout=1.0)

        assert result is True
        assert poll_count >= 2

    def test_wait_for_tray_open_timeout(self, mock_hardware):
        """Test wait_for_tray_open returns False on timeout."""
        sm = NimbieStateMachine(
            target_drive="1", hardware=mock_hardware, poll_interval=0.01
        )

        # Tray never opens
        mock_hardware.get_state.return_value = {
            "tray_out": False,
            "disk_available": True,
            "disk_in_open_tray": False,
            "disk_lifted": False,
        }

        start = time.time()
        result = sm.wait_for_tray_open(timeout=0.1)
        elapsed = time.time() - start

        assert result is False
        assert elapsed >= 0.1
        assert mock_hardware.get_state.call_count > 5

    def test_wait_for_tray_close_success(self, mock_hardware):
        """Test wait_for_tray_close succeeds when tray closes."""
        sm = NimbieStateMachine(
            target_drive="1", hardware=mock_hardware, poll_interval=0.01
        )

        # Start with tray open, close after 2 polls
        poll_count = 0

        def get_state_side_effect():
            nonlocal poll_count
            poll_count += 1
            return {
                "tray_out": poll_count < 2,
                "disk_available": True,
                "disk_in_open_tray": False,
                "disk_lifted": False,
            }

        mock_hardware.get_state.side_effect = get_state_side_effect

        result = sm.wait_for_tray_close(timeout=1.0)

        assert result is True
        assert poll_count >= 2

    def test_wait_for_tray_close_timeout(self, mock_hardware):
        """Test wait_for_tray_close returns False on timeout."""
        sm = NimbieStateMachine(
            target_drive="1", hardware=mock_hardware, poll_interval=0.01
        )

        # Tray stays open
        mock_hardware.get_state.return_value = {
            "tray_out": True,
            "disk_available": True,
            "disk_in_open_tray": False,
            "disk_lifted": False,
        }

        result = sm.wait_for_tray_close(timeout=0.1)

        assert result is False
        assert mock_hardware.get_state.call_count > 5

    def test_tray_methods_use_default_timeout(self, mock_hardware):
        """Test tray methods use default timeout when not specified."""
        sm = NimbieStateMachine(
            target_drive="1",
            hardware=mock_hardware,
            poll_interval=0.01,
            default_timeout=0.05,
        )

        # Tray never changes
        mock_hardware.get_state.return_value = {
            "tray_out": False,
            "disk_available": True,
            "disk_in_open_tray": False,
            "disk_lifted": False,
        }

        start = time.time()
        result = sm.wait_for_tray_open()  # No timeout specified
        elapsed = time.time() - start

        assert result is False
        assert (
            0.04 <= elapsed <= 0.07
        )  # Should use default timeout (with some tolerance)


class TestDiskOperationPolling:
    """Test disk-specific polling methods."""

    @pytest.fixture
    def mock_hardware(self):
        """Create a mock hardware instance."""
        hardware = MagicMock()
        # Default state - no disk operations
        hardware.get_state.return_value = {
            "disk_available": True,
            "disk_in_open_tray": False,
            "disk_lifted": False,
            "tray_out": False,
        }
        return hardware

    def test_wait_for_disk_placed_success(self, mock_hardware):
        """Test wait_for_disk_placed succeeds when disk is placed."""
        sm = NimbieStateMachine(
            target_drive="1", hardware=mock_hardware, poll_interval=0.01
        )

        # Simulate disk placement after 2 polls
        poll_count = 0

        def get_state_side_effect():
            nonlocal poll_count
            poll_count += 1
            return {
                "tray_out": True,  # Tray must be open
                "disk_in_open_tray": poll_count >= 2,
                "disk_lifted": False,
                "disk_available": True,
            }

        mock_hardware.get_state.side_effect = get_state_side_effect

        result = sm.wait_for_disk_placed(timeout=1.0)

        assert result is True
        assert poll_count >= 2

    def test_wait_for_disk_placed_timeout(self, mock_hardware):
        """Test wait_for_disk_placed returns False on timeout."""
        sm = NimbieStateMachine(
            target_drive="1", hardware=mock_hardware, poll_interval=0.01
        )

        # Disk never placed
        mock_hardware.get_state.return_value = {
            "tray_out": True,
            "disk_in_open_tray": False,
            "disk_lifted": False,
            "disk_available": True,
        }

        result = sm.wait_for_disk_placed(timeout=0.1)

        assert result is False
        assert mock_hardware.get_state.call_count > 5

    def test_wait_for_disk_lifted_success(self, mock_hardware):
        """Test wait_for_disk_lifted succeeds when disk is lifted."""
        sm = NimbieStateMachine(
            target_drive="1", hardware=mock_hardware, poll_interval=0.01
        )

        # Simulate disk lifting after 3 polls
        poll_count = 0

        def get_state_side_effect():
            nonlocal poll_count
            poll_count += 1
            return {
                "tray_out": True,
                "disk_in_open_tray": poll_count < 3,  # Disk disappears when lifted
                "disk_lifted": poll_count >= 3,
                "disk_available": True,
            }

        mock_hardware.get_state.side_effect = get_state_side_effect

        result = sm.wait_for_disk_lifted(timeout=1.0)

        assert result is True
        assert poll_count >= 3

    def test_wait_for_disk_lifted_timeout(self, mock_hardware):
        """Test wait_for_disk_lifted returns False on timeout."""
        sm = NimbieStateMachine(
            target_drive="1", hardware=mock_hardware, poll_interval=0.01
        )

        # Disk never lifted
        mock_hardware.get_state.return_value = {
            "tray_out": True,
            "disk_in_open_tray": True,
            "disk_lifted": False,
            "disk_available": True,
        }

        result = sm.wait_for_disk_lifted(timeout=0.1)

        assert result is False

    def test_wait_for_disk_dropped_success(self, mock_hardware):
        """Test wait_for_disk_dropped succeeds when disk is dropped."""
        sm = NimbieStateMachine(
            target_drive="1", hardware=mock_hardware, poll_interval=0.01
        )

        # Start with disk lifted, drop after 2 polls
        poll_count = 0

        def get_state_side_effect():
            nonlocal poll_count
            poll_count += 1
            return {
                "tray_out": False,  # Tray closed for drop
                "disk_in_open_tray": False,
                "disk_lifted": poll_count < 2,  # Lifted then dropped
                "disk_available": True,
            }

        mock_hardware.get_state.side_effect = get_state_side_effect

        result = sm.wait_for_disk_dropped(timeout=1.0)

        assert result is True
        assert poll_count >= 2

    def test_wait_for_disk_dropped_timeout(self, mock_hardware):
        """Test wait_for_disk_dropped returns False on timeout."""
        sm = NimbieStateMachine(
            target_drive="1", hardware=mock_hardware, poll_interval=0.01
        )

        # Disk stays lifted
        mock_hardware.get_state.return_value = {
            "tray_out": False,
            "disk_in_open_tray": False,
            "disk_lifted": True,  # Always lifted
            "disk_available": True,
        }

        result = sm.wait_for_disk_dropped(timeout=0.1)

        assert result is False

    def test_wait_for_disk_in_drive_success(self, mock_hardware):
        """Test wait_for_disk_in_drive succeeds when disk loads."""
        sm = NimbieStateMachine(
            target_drive="1", hardware=mock_hardware, poll_interval=0.01
        )

        # Simulate disk loading process
        poll_count = 0

        def get_state_side_effect():
            nonlocal poll_count
            poll_count += 1
            if poll_count < 2:
                # Disk in tray, tray open
                return {
                    "tray_out": True,
                    "disk_in_open_tray": True,
                    "disk_lifted": False,
                    "disk_available": True,
                }
            # Tray closed, disk loaded
            return {
                "tray_out": False,
                "disk_in_open_tray": False,
                "disk_lifted": False,
                "disk_available": True,
            }

        mock_hardware.get_state.side_effect = get_state_side_effect

        result = sm.wait_for_disk_in_drive(timeout=1.0)

        assert result is True
        assert poll_count >= 2

    def test_wait_for_disk_in_drive_timeout(self, mock_hardware):
        """Test wait_for_disk_in_drive returns False on timeout."""
        sm = NimbieStateMachine(
            target_drive="1", hardware=mock_hardware, poll_interval=0.01
        )

        # Tray stays open
        mock_hardware.get_state.return_value = {
            "tray_out": True,  # Tray never closes
            "disk_in_open_tray": True,
            "disk_lifted": False,
            "disk_available": True,
        }

        result = sm.wait_for_disk_in_drive(timeout=0.1)

        assert result is False

    def test_disk_in_drive_requires_all_conditions(self, mock_hardware):
        """Test that disk_in_drive requires all conditions to be met."""
        sm = NimbieStateMachine(
            target_drive="1", hardware=mock_hardware, poll_interval=0.01
        )

        # Test various incomplete states
        incomplete_states = [
            # Tray still open
            {"tray_out": True, "disk_in_open_tray": False, "disk_lifted": False},
            # Disk still in tray
            {"tray_out": False, "disk_in_open_tray": True, "disk_lifted": False},
            # Disk still lifted
            {"tray_out": False, "disk_in_open_tray": False, "disk_lifted": True},
        ]

        for state in incomplete_states:
            state["disk_available"] = True
            mock_hardware.get_state.return_value = state

            result = sm.wait_for_disk_in_drive(timeout=0.05)
            assert result is False
