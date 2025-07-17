"""Tests for the pure state machine implementation."""

import pytest
from unittest.mock import Mock, patch, call
import logging

from nimbie.pure_state_machine import NimbiePureStateMachine
from nimbie.driver import NimbieDriver


class TestNimbiePureStateMachine:
    """Test the pure state machine implementation."""

    @pytest.fixture
    def mock_hardware(self):
        """Create a mock hardware driver."""
        mock = Mock(spec=NimbieDriver)
        # Default state
        mock.get_state.return_value = {
            'disk_available': True,
            'disk_lifted': False,
            'tray_out': False,
            'disk_in_open_tray': False,
        }
        mock.disk_available.return_value = True
        return mock

    @pytest.fixture
    def state_machine(self, mock_hardware):
        """Create a state machine with mock hardware."""
        sm = NimbiePureStateMachine(
            target_drive="1",
            hardware=mock_hardware,
            poll_interval=0.01,  # Fast polling for tests
            default_timeout=1.0,  # Short timeout for tests
            log_level=logging.WARNING
        )
        return sm

    def test_initial_state(self, state_machine):
        """Test that state machine starts in initializing state."""
        assert state_machine.state == 'initializing'
        assert state_machine.state.startswith('initializing_')

    def test_initialize_success(self, state_machine, mock_hardware):
        """Test successful initialization."""
        # Initialize should check hardware and transition to ready
        result = state_machine.initialize()
        
        assert result is True
        assert state_machine.state == 'ready'
        
        # Verify hardware was checked
        assert mock_hardware.get_state.called

    def test_initialize_with_lifted_disk(self, state_machine, mock_hardware):
        """Test initialization clears lifted disk."""
        # Set up hardware state with lifted disk
        mock_hardware.get_state.return_value = {
            'disk_available': True,
            'disk_lifted': True,
            'tray_out': False,
            'disk_in_open_tray': False,
        }
        
        result = state_machine.initialize()
        
        assert result is True
        assert state_machine.state == 'ready'
        
        # Verify disk was rejected
        mock_hardware.reject_disk.assert_called_once()

    def test_initialize_with_open_tray(self, state_machine, mock_hardware):
        """Test initialization handles open tray."""
        # Set up hardware state with open tray
        mock_hardware.get_state.return_value = {
            'disk_available': True,
            'disk_lifted': False,
            'tray_out': True,
            'disk_in_open_tray': False,
        }
        
        # Mock tray closing
        def update_tray_state(*args):
            mock_hardware.get_state.return_value['tray_out'] = False
            return True
        
        mock_hardware.close_tray.side_effect = update_tray_state
        
        result = state_machine.initialize()
        
        assert result is True
        assert state_machine.state == 'ready'
        
        # Verify tray was closed
        mock_hardware.close_tray.assert_called()

    def test_load_next_disk_not_ready(self, state_machine):
        """Test load_next_disk fails when not in ready state."""
        # State machine is in initializing state
        result = state_machine.load_next_disk()
        
        assert result is False

    def test_load_next_disk_no_disk_available(self, state_machine, mock_hardware):
        """Test load_next_disk fails when no disk available."""
        # Initialize first
        state_machine.initialize()
        assert state_machine.state == 'ready'
        
        # No disk available
        mock_hardware.disk_available.return_value = False
        
        result = state_machine.load_next_disk()
        
        assert result is False
        assert state_machine.state == 'ready'  # Should stay in ready

    def test_load_next_disk_success(self, state_machine, mock_hardware):
        """Test successful disk loading."""
        # Initialize first
        state_machine.initialize()
        assert state_machine.state == 'ready'
        
        # Mock the loading sequence
        tray_open_count = 0
        disk_placed_count = 0
        
        def handle_open_tray():
            nonlocal tray_open_count
            tray_open_count += 1
            if tray_open_count > 2:  # After a few checks
                mock_hardware.get_state.return_value['tray_out'] = True
        
        def handle_place_disk():
            nonlocal disk_placed_count
            disk_placed_count += 1
            if disk_placed_count > 2:  # After a few checks
                mock_hardware.get_state.return_value['disk_in_open_tray'] = True
        
        def handle_close_tray():
            mock_hardware.get_state.return_value['tray_out'] = False
            mock_hardware.get_state.return_value['disk_in_open_tray'] = False
        
        mock_hardware.open_tray.side_effect = handle_open_tray
        mock_hardware.place_disk.side_effect = handle_place_disk
        mock_hardware.close_tray.side_effect = handle_close_tray
        
        result = state_machine.load_next_disk()
        
        assert result is True
        assert state_machine.state == 'processing'
        
        # Verify hardware calls
        mock_hardware.open_tray.assert_called()
        mock_hardware.place_disk.assert_called()
        mock_hardware.close_tray.assert_called()

    def test_accept_current_disk(self, state_machine, mock_hardware):
        """Test accepting current disk."""
        # Get to processing state first
        state_machine.initialize()
        
        # Mock loading
        mock_hardware.get_state.return_value['tray_out'] = True
        state_machine.load_next_disk()
        mock_hardware.get_state.return_value['disk_in_open_tray'] = True
        mock_hardware.get_state.return_value['tray_out'] = False
        
        # Force state to processing for test
        state_machine.state = 'processing'
        
        # Mock unloading sequence
        def handle_lift():
            mock_hardware.get_state.return_value['disk_lifted'] = True
        
        mock_hardware.lift_disk.side_effect = handle_lift
        
        result = state_machine.accept_current_disk()
        
        assert result is True
        assert state_machine.state == 'ready'
        
        # Verify accept path was taken
        mock_hardware.accept_disk.assert_called_once()
        mock_hardware.reject_disk.assert_not_called()

    def test_reject_current_disk(self, state_machine, mock_hardware):
        """Test rejecting current disk."""
        # Get to processing state
        state_machine.state = 'processing'
        
        # Mock unloading sequence
        mock_hardware.get_state.return_value['tray_out'] = True
        mock_hardware.get_state.return_value['disk_lifted'] = True
        
        result = state_machine.reject_current_disk()
        
        assert result is True
        assert state_machine.state == 'ready'
        
        # Verify reject path was taken
        mock_hardware.reject_disk.assert_called_once()
        mock_hardware.accept_disk.assert_not_called()

    def test_state_queries(self, state_machine):
        """Test state query methods."""
        # Initial state
        assert state_machine.is_ready() is False
        assert state_machine.is_processing() is False
        assert state_machine.is_loading() is False
        
        # Ready state
        state_machine.state = 'ready'
        assert state_machine.is_ready() is True
        assert state_machine.is_processing() is False
        
        # Processing state
        state_machine.state = 'processing'
        assert state_machine.is_ready() is False
        assert state_machine.is_processing() is True
        
        # Loading sub-state
        state_machine.state = 'loading_opening_tray'
        assert state_machine.is_loading() is True

    def test_can_load_disk(self, state_machine, mock_hardware):
        """Test can_load_disk query."""
        # Not ready
        assert state_machine.can_load_disk() is False
        
        # Ready but no disk
        state_machine.state = 'ready'
        mock_hardware.disk_available.return_value = False
        assert state_machine.can_load_disk() is False
        
        # Ready with disk
        mock_hardware.disk_available.return_value = True
        assert state_machine.can_load_disk() is True

    def test_error_state_transition(self, state_machine):
        """Test transition to error state."""
        state_machine.state = 'ready'
        
        # Trigger error
        state_machine.to_error()
        
        assert state_machine.state == 'error'

    def test_recovery_from_error(self, state_machine, mock_hardware):
        """Test recovery from error state."""
        # Put in error state
        state_machine.state = 'error'
        
        # Recover
        result = state_machine.recover()
        
        assert state_machine.state == 'ready'
        # Hardware should be checked during recovery
        mock_hardware.get_state.assert_called()

    def test_cleanup(self, state_machine, mock_hardware):
        """Test resource cleanup."""
        # Close should clean up hardware
        state_machine.close()
        
        # Verify hardware was closed
        mock_hardware.close.assert_called_once()
        
        # Hardware reference should be None
        assert state_machine.hardware is None


@pytest.mark.hardware
class TestNimbiePureStateMachineHardware:
    """Hardware tests for pure state machine."""

    @pytest.fixture
    def state_machine(self):
        """Create state machine with real hardware."""
        sm = NimbiePureStateMachine(
            target_drive="1",
            poll_interval=0.1,
            default_timeout=30.0,
            log_level=logging.INFO
        )
        yield sm
        # Cleanup
        sm.close()

    def test_initialize_with_hardware(self, state_machine):
        """Test initialization with real hardware."""
        result = state_machine.initialize()
        
        assert result is True
        assert state_machine.state == 'ready'

    def test_full_cycle_with_hardware(self, state_machine):
        """Test full load/accept cycle with real hardware."""
        # Initialize
        assert state_machine.initialize() is True
        
        if not state_machine.can_load_disk():
            pytest.skip("No disk available in hardware")
        
        # Load disk
        assert state_machine.load_next_disk() is True
        assert state_machine.state == 'processing'
        
        # Accept disk
        assert state_machine.accept_current_disk() is True
        assert state_machine.state == 'ready'

    def test_error_recovery_with_hardware(self, state_machine):
        """Test error recovery with real hardware."""
        # Initialize
        assert state_machine.initialize() is True
        
        # Force error state
        state_machine.to_error()
        assert state_machine.state == 'error'
        
        # Recover
        state_machine.recover()
        assert state_machine.state == 'ready'
        
        # Verify we can still operate
        hw_state = state_machine.hardware.get_state()
        assert hw_state is not None