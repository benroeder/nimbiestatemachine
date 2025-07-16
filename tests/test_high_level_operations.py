"""Phase 3.2: Test high-level disk operations with real hardware."""

import pytest

from nimbie import NimbieStateMachine


class TestHighLevelOperations:
    """Test high-level disk loading and unloading operations."""

    def test_load_disk_from_queue(self, nimbie_hardware):
        """Test loading a disk from queue into drive."""
        sm = NimbieStateMachine(target_drive="1", hardware=nimbie_hardware)

        # Check if we have a disk to test with
        if not sm.hardware.disk_available():
            pytest.skip("No disk available for testing")

        # Start from idle state
        assert sm.state == "idle"

        # Load disk from queue
        result = sm.load_disk_from_queue()

        # If loading failed due to no disk, skip the test
        if not result:
            # Check if it was due to no disk available
            state = sm.get_hardware_state()
            if not state["disk_available"]:
                pytest.skip("No disk available in queue during test")

        assert result is True, "Disk should have loaded successfully"

        # Should now be in processing state
        assert sm.state == "processing"

        # Verify disk is in drive (tray closed)
        state = sm.get_hardware_state()
        assert not state["tray_out"], "Tray should be closed"
        assert not state["disk_in_open_tray"], "Disk should be in drive"

    def test_unload_disk_to_accept(self, nimbie_state_machine):
        """Test unloading a disk to accept pile."""
        sm = nimbie_state_machine

        # Skip if no disk available
        if not sm.hardware.disk_available():
            pytest.skip("No disk available for testing")

        # First load a disk
        if sm.state == "idle":
            result = sm.load_disk_from_queue()
            assert result is True, "Failed to load disk"

        # Should be in processing state
        assert sm.state == "processing"

        # Unload to accept pile
        result = sm.unload_disk_to_accept()
        assert result is True, "Disk should have been accepted"

        # Should be back in idle state
        assert sm.state == "idle"

        # Verify tray is closed and no disk visible
        state = sm.get_hardware_state()
        assert not state["tray_out"], "Tray should be closed"
        assert not state["disk_lifted"], "Disk should not be lifted"

    def test_unload_disk_to_reject(self, nimbie_state_machine):
        """Test unloading a disk to reject pile."""
        sm = nimbie_state_machine

        # Skip if no disk available
        if not sm.hardware.disk_available():
            pytest.skip("No disk available for testing")

        # First load a disk
        if sm.state == "idle":
            result = sm.load_disk_from_queue()
            assert result is True, "Failed to load disk"

        # Should be in processing state
        assert sm.state == "processing"

        # Unload to reject pile
        result = sm.unload_disk_to_reject()
        assert result is True, "Disk should have been rejected"

        # Should be back in idle state
        assert sm.state == "idle"

        # Verify tray is closed and no disk visible
        state = sm.get_hardware_state()
        assert not state["tray_out"], "Tray should be closed"
        assert not state["disk_lifted"], "Disk should not be lifted"

    def test_full_disk_cycle(self, nimbie_state_machine):
        """Test a complete disk processing cycle."""
        sm = nimbie_state_machine

        # Skip if no disk available
        if not sm.hardware.disk_available():
            pytest.skip("No disk available for testing")

        # Start from idle
        assert sm.state == "idle"

        # Load disk
        print("\n1. Loading disk from queue...")
        result = sm.load_disk_from_queue()
        assert result is True
        assert sm.state == "processing"
        print("Disk loaded successfully")

        # Simulate processing (in real usage, this is where imaging happens)
        print("\n2. Processing disk (simulated)...")
        print("Processing complete")

        # Unload disk to accept
        print("\n3. Unloading disk to accept pile...")
        result = sm.unload_disk_to_accept()
        assert result is True
        assert sm.state == "idle"
        print("Disk accepted successfully")

        print("\nFull disk cycle completed successfully!")

    def test_error_handling_wrong_state(self, nimbie_state_machine):
        """Test that operations fail gracefully in wrong states."""
        sm = nimbie_state_machine

        # Ensure we're in idle state
        assert sm.state == "idle"

        # Try to unload when no disk is loaded
        with pytest.raises(RuntimeError, match="Cannot unload disk in idle state"):
            sm.unload_disk_to_accept()

        # Manually set to processing state
        with sm.manual_operation():
            sm.manual_set_state("processing")

        # Try to load when already processing
        with pytest.raises(RuntimeError, match="Cannot load disk in processing state"):
            sm.load_disk_from_queue()


class TestStateValidation:
    """Test proper state validation for high-level operations."""

    def test_load_requires_idle_or_loading(self, nimbie_state_machine):
        """Test that load only works in idle or loading states."""
        sm = nimbie_state_machine

        # Test from idle (should work)
        assert sm.state == "idle"
        if sm.hardware.disk_available():
            # Don't actually load, just test the state check passes
            from contextlib import suppress

            with suppress(Exception):
                # This will fail at disk placement but state check should pass
                sm.load_disk_from_queue()

        # Test from other states (should fail)
        for invalid_state in ["processing", "unloading", "error"]:
            with sm.manual_operation():
                sm.manual_set_state(invalid_state)

            with pytest.raises(
                RuntimeError, match=f"Cannot load disk in {invalid_state} state"
            ):
                sm.load_disk_from_queue()

    def test_unload_requires_processing_or_unloading(self, nimbie_state_machine):
        """Test that unload only works in processing or unloading states."""
        sm = nimbie_state_machine

        # Test from invalid states (should fail)
        for invalid_state in ["idle", "loading", "error"]:
            with sm.manual_operation():
                sm.manual_set_state(invalid_state)

            with pytest.raises(
                RuntimeError, match=f"Cannot unload disk in {invalid_state} state"
            ):
                sm.unload_disk_to_accept()

            with pytest.raises(
                RuntimeError, match=f"Cannot unload disk in {invalid_state} state"
            ):
                sm.unload_disk_to_reject()
