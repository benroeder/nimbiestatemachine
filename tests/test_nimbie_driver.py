"""Test suite for nimbie_driver.py - the clean hardware interface."""

import inspect
import time
from collections.abc import Generator
from unittest.mock import MagicMock

import pytest

from nimbie import NimbieDriver
from nimbie.driver import (
    DiskInTrayError,
    DropperError,
    HardwareStateError,
    NoDiskError,
    NoDiskInTrayError,
    TrayInvalidStateError,
)

# Mark for hardware tests
pytestmark = pytest.mark.hardware


@pytest.fixture(scope="module")
def nimbie_driver() -> Generator[NimbieDriver, None, None]:
    """Provide a NimbieDriver instance for testing."""
    try:
        driver = NimbieDriver(target_drive="1")
        yield driver
    except Exception as e:
        pytest.skip(f"Hardware not available: {e}")


class TestNimbieDriverBasics:
    """Test basic driver functionality."""

    def test_driver_connects(self, nimbie_driver: NimbieDriver) -> None:
        """Test that driver can connect to hardware."""
        # Use the fixture which already has a connected driver
        driver = nimbie_driver
        assert driver is not None
        assert driver.in_ep is not None
        assert driver.out_ep is not None

    def test_driver_has_no_sleep(self) -> None:
        """Verify the driver doesn't use sleep."""
        import nimbie.driver as nimbie_driver

        # Check module source
        source = inspect.getsource(nimbie_driver)
        assert "import time" not in source
        assert "from time import" not in source
        assert "sleep(" not in source

    def test_get_state_structure(self, nimbie_driver: NimbieDriver) -> None:
        """Test that get_state returns correct structure."""
        driver = nimbie_driver
        try:
            state = driver.get_state()
        except Exception as e:
            if "Access denied" in str(e) or "Operation timed out" in str(e):
                pytest.skip(f"Hardware access issue: {e}")
            raise

        # Verify state structure
        assert isinstance(state, dict)
        assert "disk_available" in state
        assert "disk_in_open_tray" in state
        assert "disk_lifted" in state
        assert "tray_out" in state

        # Verify boolean values
        for key, value in state.items():
            assert isinstance(value, bool), f"{key} should be bool, got {type(value)}"


class TestNimbieDriverCommands:
    """Test hardware commands return immediately without polling."""

    @pytest.fixture
    def driver(self, nimbie_driver: NimbieDriver) -> NimbieDriver:
        """Use the module-scoped driver instance."""
        return nimbie_driver

    def test_tray_commands_return_immediately(self, driver: NimbieDriver) -> None:
        """Test that tray commands return without waiting."""
        # Mock the eject functions to measure timing
        driver._open_tray_fn = MagicMock()
        driver._close_tray_fn = MagicMock()

        # Test open tray
        start = time.time()
        driver.open_tray()
        elapsed = time.time() - start
        assert elapsed < 0.1, f"open_tray took {elapsed}s, should be instant"
        driver._open_tray_fn.assert_called_once()

        # Test close tray
        start = time.time()
        driver.close_tray()
        elapsed = time.time() - start
        assert elapsed < 0.1, f"close_tray took {elapsed}s, should be instant"
        driver._close_tray_fn.assert_called_once()

    def test_disk_available(self, driver: NimbieDriver) -> None:
        """Test disk_available method."""
        try:
            available = driver.disk_available()
            assert isinstance(available, bool)
        except Exception as e:
            if "Access denied" in str(e) or "Operation timed out" in str(e):
                pytest.skip(f"Hardware access issue: {e}")
            raise

    def test_place_disk_error_handling(self, driver: NimbieDriver) -> None:
        """Test that place_disk raises appropriate errors."""
        # If no disk available, should raise NoDiskError
        try:
            if not driver.disk_available():
                with pytest.raises(NoDiskError):
                    driver.place_disk()
        except Exception as e:
            if "Access denied" in str(e) or "Operation timed out" in str(e):
                pytest.skip(f"Hardware access issue: {e}")
            raise

    def test_lift_disk_error_handling(self, driver: NimbieDriver) -> None:
        """Test that lift_disk raises appropriate errors."""
        try:
            state = driver.get_state()

            # If no disk in tray, should raise error
            if not state["disk_in_open_tray"] and not state["disk_lifted"]:
                with pytest.raises((NoDiskInTrayError, TrayInvalidStateError)):
                    driver.lift_disk()
        except Exception as e:
            if "Access denied" in str(e) or "Operation timed out" in str(e):
                pytest.skip(f"Hardware access issue: {e}")
            raise


class TestNimbieDriverStatusCodes:
    """Test status code handling."""

    def test_decode_success_codes(self) -> None:
        """Test decoding of success status codes."""
        result = NimbieDriver.decode_statuscode("AT+O")
        assert isinstance(result, str)
        assert "success" in result.lower()

        result = NimbieDriver.decode_statuscode("AT+S07")
        assert isinstance(result, str)
        assert "placed" in result.lower()

    def test_decode_error_codes(self) -> None:
        """Test decoding of error status codes."""
        # Test disk in tray error
        result = NimbieDriver.decode_statuscode("AT+S12")
        assert isinstance(result, DiskInTrayError)

        # Test no disk in queue error
        result = NimbieDriver.decode_statuscode("AT+S14")
        assert isinstance(result, NoDiskError)

        # Test tray wrong state error
        result = NimbieDriver.decode_statuscode("AT+S10")
        assert isinstance(result, TrayInvalidStateError)

        # Test dropper error
        result = NimbieDriver.decode_statuscode("AT+S03")
        assert isinstance(result, DropperError)

        # Test no disk in tray error
        result = NimbieDriver.decode_statuscode("AT+S00")
        assert isinstance(result, NoDiskInTrayError)

        # Test unknown error
        result = NimbieDriver.decode_statuscode("AT+E09")
        assert isinstance(result, HardwareStateError)

    def test_extract_statuscode(self) -> None:
        """Test status code extraction from response."""
        # Test valid response
        response = ["", "AT+S07", ""]
        code = NimbieDriver.extract_statuscode(response)
        assert code == "AT+S07"

        # Test no status code
        response = ["", "some other message", ""]
        with pytest.raises(ValueError):
            NimbieDriver.extract_statuscode(response)


class TestNimbieDriverAPI:
    """Test that the driver API is minimal and clean."""

    def test_public_api(self, nimbie_driver: NimbieDriver) -> None:
        """Test that only intended methods are public."""
        driver = nimbie_driver

        # Expected public methods
        expected_public = {
            "send_command",
            "get_response",
            "extract_statuscode",
            "array_to_string",
            "read_data",
            "read",
            "decode_statuscode",
            "try_command",
            "place_disk",
            "lift_disk",
            "accept_disk",
            "reject_disk",
            "get_state",
            "disk_available",
            "open_tray",
            "close_tray",
            "reset_usb",
        }

        # Get all public methods (not starting with _)
        public_methods = {
            name
            for name in dir(driver)
            if not name.startswith("_") and callable(getattr(driver, name))
        }

        # Remove inherited methods
        public_methods -= {
            "__class__",
            "__delattr__",
            "__dict__",
            "__dir__",
            "__doc__",
            "__eq__",
            "__format__",
            "__ge__",
            "__getattribute__",
            "__gt__",
            "__hash__",
            "__init__",
            "__init_subclass__",
            "__le__",
            "__lt__",
            "__module__",
            "__ne__",
            "__new__",
            "__reduce__",
            "__reduce_ex__",
            "__repr__",
            "__setattr__",
            "__sizeof__",
            "__str__",
            "__subclasshook__",
            "__weakref__",
        }

        # Check we have exactly the expected methods
        assert public_methods == expected_public, (
            f"Unexpected public methods: {public_methods - expected_public}"
        )

    def test_no_high_level_methods(self, nimbie_driver: NimbieDriver) -> None:
        """Verify driver doesn't have high-level workflow methods."""
        driver = nimbie_driver

        # These methods should NOT exist in the clean driver
        forbidden_methods = [
            "load_next_disk",
            "accept_current_disk",
            "reject_current_disk",
            "map_over_disks",
            "map_over_disks_forever",
            "maybe_open_tray",
            "maybe_close_tray",
        ]

        for method in forbidden_methods:
            assert not hasattr(driver, method), (
                f"Driver should not have {method} method"
            )


class TestNimbieDriverDocumentation:
    """Test that all methods are properly documented."""

    def test_all_methods_have_docstrings(self, nimbie_driver: NimbieDriver) -> None:
        """Verify all public methods have docstrings."""
        driver = nimbie_driver

        for name in dir(driver):
            if not name.startswith("_") and name != "__init__":
                obj = getattr(driver, name)
                if callable(obj):
                    assert obj.__doc__ is not None, f"{name} missing docstring"
                    # Docstring should mention polling if applicable
                    if name in ["place_disk", "lift_disk", "open_tray", "close_tray"]:
                        assert (
                            "poll" in obj.__doc__.lower()
                            or "wait" in obj.__doc__.lower()
                        ), f"{name} docstring should mention caller must poll"
