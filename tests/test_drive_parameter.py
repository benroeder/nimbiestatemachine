"""Test drive parameter functionality."""

from unittest.mock import Mock, patch

import pytest

from nimbie import NimbieDriver, NimbieStateMachine


def test_eject_requires_drive_parameter():
    """Test that eject functions require drive parameter."""
    from nimbie.eject import close_tray, open_tray

    # Test that open_tray requires drive parameter
    with pytest.raises(TypeError) as exc_info:
        open_tray()
    assert "missing 1 required positional argument: 'drive'" in str(exc_info.value)

    # Test that close_tray requires drive parameter
    with pytest.raises(TypeError) as exc_info:
        close_tray()
    assert "missing 1 required positional argument: 'drive'" in str(exc_info.value)


def test_eject_with_drive_parameter():
    """Test that eject functions pass drive parameter correctly."""
    import platform

    from nimbie.eject import close_tray, open_tray

    # Mock subprocess.run
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0

        # Test open_tray with drive
        open_tray(drive="1")

        # Check platform to verify correct command
        if "Darwin" in platform.system():
            assert mock_run.call_args[0][0] == [
                "drutil",
                "-drive",
                "1",
                "tray",
                "eject",
            ]
        else:
            assert mock_run.call_args[0][0] == ["eject", "1"]

        # Test close_tray with drive
        close_tray(drive="/dev/sr0")

        # Check platform to verify correct command
        if "Darwin" in platform.system():
            assert mock_run.call_args[0][0] == [
                "drutil",
                "-drive",
                "/dev/sr0",
                "tray",
                "close",
            ]
        else:
            assert mock_run.call_args[0][0] == ["eject", "-t", "/dev/sr0"]


def test_eject_error_messages():
    """Test that error messages include drive info."""
    from nimbie.eject import close_tray, open_tray

    # Mock subprocess.run to simulate failure
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 1

        # Test error with drive
        with pytest.raises(Exception) as exc_info:
            open_tray(drive="2")
        assert str(exc_info.value) == "Failed to open tray for drive 2"

        # Test close tray error
        with pytest.raises(Exception) as exc_info:
            close_tray(drive="/dev/sr1")
        assert str(exc_info.value) == "Failed to close tray for drive /dev/sr1"


def test_nimbie_driver_with_target_drive():
    """Test that NimbieDriver passes target_drive to eject functions."""
    # Mock USB device
    with patch("usb.core.find") as mock_find:
        mock_device = Mock()
        mock_device.set_configuration = Mock()
        mock_device.get_active_configuration = Mock(return_value={(0, 0): Mock()})
        mock_find.return_value = mock_device

        # Mock usb.util.find_descriptor
        with patch("usb.util.find_descriptor") as mock_descriptor:
            mock_descriptor.return_value = Mock()

            # Mock eject functions
            with (
                patch("nimbie.eject.open_tray") as mock_open,
                patch("nimbie.eject.close_tray") as mock_close,
            ):
                # Create driver with target_drive
                driver = NimbieDriver(target_drive="1")

                # Call open_tray through driver
                driver.open_tray()

                # Verify open_tray was called with correct drive
                mock_open.assert_called_once_with("2")

                # Call close_tray through driver
                driver.close_tray()

                # Verify close_tray was called with correct drive
                mock_close.assert_called_once_with("2")


def test_state_machine_with_target_drive():
    """Test that NimbieStateMachine passes target_drive to driver."""
    # Mock USB device
    with patch("usb.core.find") as mock_find:
        mock_device = Mock()
        mock_device.set_configuration = Mock()
        mock_device.get_active_configuration = Mock(return_value={(0, 0): Mock()})
        mock_find.return_value = mock_device

        # Mock usb.util.find_descriptor
        with patch("usb.util.find_descriptor") as mock_descriptor:
            mock_descriptor.return_value = Mock()

            # Create state machine with target_drive
            sm = NimbieStateMachine(target_drive="/dev/sr0")

            # Verify driver has correct target_drive
            assert sm.hardware.target_drive == "/dev/sr0"


def test_state_machine_requires_target_drive():
    """Test that state machine requires target_drive."""
    # Mock USB device
    with patch("usb.core.find") as mock_find:
        mock_device = Mock()
        mock_device.set_configuration = Mock()
        mock_device.get_active_configuration = Mock(return_value={(0, 0): Mock()})
        mock_find.return_value = mock_device

        # Mock usb.util.find_descriptor
        with patch("usb.util.find_descriptor") as mock_descriptor:
            mock_descriptor.return_value = Mock()

            # Create state machine without target_drive should fail
            with pytest.raises(TypeError) as exc_info:
                NimbieStateMachine()
            assert "missing 1 required positional argument: 'target_drive'" in str(
                exc_info.value
            )
