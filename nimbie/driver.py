"""Clean Nimbie hardware driver - commands only, no waiting or polling.

This driver provides a minimal interface to the Nimbie hardware. It sends
commands and returns immediately. All polling, waiting, and orchestration
is handled by the state machine.

Architecture principles:
1. NO hardcoded sleeps - all timing via polling in state machine
2. Driver sends commands only - no waiting or polling
3. Returns raw responses for state machine to interpret
4. Single responsibility - hardware communication only
"""

from typing import TYPE_CHECKING, Callable, Optional, Union

import usb.core
import usb.util

if TYPE_CHECKING:
    from usb.core import array as USBArray
else:
    # USB array type
    USBArray = usb.util.array.array

# Largest incoming packet in bytes as listed in the endpoint descriptor
IN_SIZE = 64

# Nimbie command codes
CMD_PLACE_DISK = 0x52  # Place disk from queue onto tray
CMD_LIFT_DISK = 0x47  # Lift disk from tray
CMD_ACCEPT_DISK = 0x52  # Drop lifted disk to accept pile (same as place)
CMD_REJECT_DISK = 0x52  # Drop lifted disk to reject pile (same as place)
CMD_GET_STATE = 0x43  # Get hardware state

# Nimbie command parameters
PARAM_PLACE = 0x01  # Parameter for placing disk
PARAM_ACCEPT = 0x02  # Parameter for accepting disk
PARAM_REJECT = 0x03  # Parameter for rejecting disk
PARAM_LIFT = 0x01  # Parameter for lifting disk

# Nimbie status codes
STATUS_DISK_IN_TRAY = "S12"  # The tray already has a disk
STATUS_NO_DISK_IN_QUEUE = "S14"  # No disk in disk queue
STATUS_TRAY_WRONG_STATE = "S10"  # Tray is in opposite state
STATUS_DROPPER_ERROR = "S03"  # Dropper has an error
STATUS_NO_DISK_IN_TRAY = "S00"  # The tray has no disk
STATUS_SUCCESS = "O"  # Dropper success
STATUS_PLACE_SUCCESS = "S07"  # Successfully placed disk
STATUS_UNKNOWN_ERROR = "E09"  # Unknown hardware error

# State bit positions (confirmed through hardware testing)
STATE_BIT_DISK_AVAILABLE = 1  # Position 1: Disk available in queue
STATE_BIT_DISK_IN_OPEN_TRAY = 3  # Position 3: Disk in open tray
STATE_BIT_DISK_LIFTED = 4  # Position 4: Disk lifted by gripper
STATE_BIT_TRAY_OUT = 5  # Position 5: Tray is out/open


# Error classes
class NotStringError(TypeError):
    """The array -> string decoder's error message."""

    pass


class HardwareStateError(Exception):
    """If the state of the hardware does not support the requested operation."""

    pass


class DiskInTrayError(HardwareStateError):
    """The tray already has a disk."""

    pass


class NoDiskInTrayError(HardwareStateError):
    """The tray has no disk in it."""

    pass


class NoDiskError(HardwareStateError):
    """No disk available in the input queue."""

    pass


class TrayInvalidStateError(HardwareStateError):
    """The tray is closed or opened when it should be the opposite."""

    pass


class DropperError(HardwareStateError):
    """An error involving the state of the dropper.

    Perhaps it is missing a disk or you're trying to place another disk
    while the dropper is still up.
    """

    pass


class NimbieDriver:
    """Clean hardware driver for Nimbie USB duplicator.

    This driver provides direct hardware commands without any polling,
    waiting, or workflow logic. All orchestration is handled by the
    state machine.
    """

    def __init__(
        self,
        target_drive: Union[str, int],
        open_tray_fn: Optional[Callable[[], None]] = None,
        close_tray_fn: Optional[Callable[[], None]] = None,
    ):
        """Initialize connection to Nimbie hardware.

        Args:
            target_drive: Required drive specifier for multi-drive systems
                         - macOS: drive index (1,2,...) as integer or string
                         - Linux: device path ("/dev/sr0", "/dev/cdrom", etc.)
            open_tray_fn: Function to open tray (defaults to eject.open_tray)
            close_tray_fn: Function to close tray (defaults to eject.close_tray)
        """
        # Import here to avoid circular imports
        if open_tray_fn is None:
            from .eject import open_tray

            def _open_tray():
                return open_tray(target_drive)

            open_tray_fn = _open_tray
        if close_tray_fn is None:
            from .eject import close_tray

            def _close_tray():
                return close_tray(target_drive)

            close_tray_fn = _close_tray

        self._open_tray_fn = open_tray_fn
        self._close_tray_fn = close_tray_fn
        self.target_drive = target_drive

        # Find and configure USB device
        self.dev = usb.core.find(idVendor=0x1723, idProduct=0x0945)
        if self.dev is None:
            raise ValueError("Nimbie device not found")

        self.dev.set_configuration()  # There's only one config so use that one

        # Get endpoints
        cfg = self.dev.get_active_configuration()
        intf = cfg[(0, 0)]

        self.in_ep = usb.util.find_descriptor(
            intf,
            custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress)
            == usb.util.ENDPOINT_IN,
        )

        self.out_ep = usb.util.find_descriptor(
            intf,
            custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress)
            == usb.util.ENDPOINT_OUT,
        )

    def send_command(self, *command: int) -> str:
        """Send a command of up to six bytes to the Nimbie.

        Args:
            command: Command bytes to send

        Returns:
            Status code from hardware

        Raises:
            Exception: If more than 6 command bytes provided
        """
        print(f"Sending command: {command}")
        if len(command) > 6:
            raise Exception("Too many arguments. Maximum of 6")

        message = bytearray(8)
        for i in range(len(command)):
            message[i + 2] = command[i]

        self.out_ep.write(message)
        response = self.get_response()
        print(f"Got response: {response}")
        return self.extract_statuscode(response)

    def get_response(self, minimum: int = 1) -> list[str]:
        """Get the Nimbie's raw response to a command.

        The nimbie sends several messages in response to a command.
        This function reads messages from the Nimbie until it receives
        an empty message.

        Args:
            minimum: Minimum number of messages to read

        Returns:
            List of response messages
        """
        messages = []

        # Get the minimum number of messages
        for _ in range(minimum):
            message = self.read()
            messages.append(message)

        # Get any more messages that aren't null
        message = self.read()
        while len(message) > 0:
            messages.append(message)
            message = self.read()
        return messages

    @staticmethod
    def extract_statuscode(response_list: list[str]) -> str:
        """Extract the Nimbie's status code from a sequence of its messages.

        The Nimbie responds to commands with status codes starting with "AT+".

        Args:
            response_list: List of response messages

        Returns:
            Status code string

        Raises:
            ValueError: If no valid status code found
        """
        # Look for any message starting with "AT+"
        for msg in response_list:
            if isinstance(msg, str) and msg.startswith("AT+"):
                return msg

        raise ValueError(
            "Expected status code starting with 'AT+' from nimbie "
            + "but did not receive it. Instead got "
            + str(response_list)
        )

    @staticmethod
    def array_to_string(array: USBArray) -> str:
        """Parse an array of integers as a null terminated ASCII string.

        Args:
            array: Array of integers to parse

        Returns:
            Parsed string

        Raises:
            NotStringError: If array is not null terminated
        """
        if len(array) == 0:
            return ""

        # Expect null termination if nonempty string
        if array[-1] != 0:
            raise NotStringError(
                "Expected array to be null terminated but got " + str(array[-1])
            )
        return "".join([chr(x) for x in array][:-1])

    def read_data(self) -> USBArray:
        """Read the next message from the Nimbie as an array of integers.

        Returns:
            Array of integers from hardware
        """
        # Maybe have the timeout be an option instead of just 20 seconds?
        return self.in_ep.read(IN_SIZE, 20000)

    def read(self) -> Union[str, USBArray]:
        """Attempt to read a null terminated string from the Nimbie.

        Returns:
            String if null terminated, otherwise array of integers
        """
        data = self.read_data()
        try:
            return self.array_to_string(data)
        except NotStringError:
            return data

    @staticmethod
    def decode_statuscode(statuscode: str) -> Union[Exception, str]:
        """Decode one of the Nimbie's status codes.

        Args:
            statuscode: Status code to decode

        Returns:
            Exception on error codes, descriptive string on success codes
        """
        print(f"Decoding status code: '{statuscode}'")
        if not statuscode.startswith("AT+"):
            print("Warning: Status code doesn't start with AT+")
        code = statuscode[3:] if len(statuscode) > 3 else statuscode

        if code == STATUS_DISK_IN_TRAY:
            return DiskInTrayError("The tray already has a disk")
        if code == STATUS_NO_DISK_IN_QUEUE:
            return NoDiskError("No disk in disk queue")
        if code == STATUS_TRAY_WRONG_STATE:
            return TrayInvalidStateError(
                "The tray is in the opposite state it should be in"
            )
        if code == STATUS_DROPPER_ERROR:
            return DropperError(
                "The dropper has an error (maybe it's "
                + "missing a disk. Maybe you're attempting "
                + "to place a disk on it while it's still up)."
            )
        if code == STATUS_NO_DISK_IN_TRAY:
            return NoDiskInTrayError("The tray has no disk in it")
        if code == STATUS_SUCCESS:
            return "Dropper success (lifting or dropping)"
        if code == STATUS_PLACE_SUCCESS:
            return "Successfully placed disk on tray"
        if code == STATUS_UNKNOWN_ERROR:
            return HardwareStateError("Unknown error E09")

        return f"Unknown status code: {code}"

    def try_command(self, *command: int) -> str:
        """Try the command, throwing an error if the Nimbie throws one.

        Args:
            command: Command bytes to send

        Returns:
            Success message

        Raises:
            HardwareStateError: If hardware returns an error
        """
        result = self.send_command(*command)
        decoded = self.decode_statuscode(result)
        if isinstance(decoded, Exception):
            raise decoded
        return decoded

    # Basic hardware commands - no waiting or polling

    def place_disk(self) -> str:
        """Place the next disk from the queue into the tray.

        Note: Does not wait for completion. Caller must poll for state change.

        Returns:
            Command result
        """
        return self.try_command(CMD_PLACE_DISK, PARAM_PLACE)

    def lift_disk(self) -> str:
        """Lift the disk from the tray.

        Note: Does not wait for completion. Caller must poll for state change.

        Returns:
            Command result
        """
        return self.try_command(CMD_LIFT_DISK, PARAM_LIFT)

    def accept_disk(self) -> str:
        """Drop the lifted disk into the accept pile.

        Note: Does not wait for completion. Caller must poll for state change.

        Returns:
            Command result
        """
        return self.try_command(CMD_ACCEPT_DISK, PARAM_ACCEPT)

    def reject_disk(self) -> str:
        """Drop the lifted disk into the reject pile.

        Note: Does not wait for completion. Caller must poll for state change.

        Returns:
            Command result
        """
        return self.try_command(CMD_REJECT_DISK, PARAM_REJECT)

    def get_state(self) -> dict[str, bool]:
        """Get the current state of the Nimbie hardware.

        Returns:
            Dictionary with boolean values:
                - disk_available: Disk available in queue
                - disk_in_open_tray: Disk in open tray
                - disk_lifted: Disk lifted by gripper
                - tray_out: Tray is out/open
        """
        # Send state command directly and get full response
        message = bytearray(8)
        message[2] = CMD_GET_STATE
        self.out_ep.write(message)
        response = self.get_response()

        # Find the state string in curly braces
        state_str = None
        for msg in response:
            if isinstance(msg, str) and msg.startswith("{") and msg.endswith("}"):
                state_str = msg[1:-1]  # Remove braces
                break

        if state_str and len(state_str) >= 7:
            # Success - show state and return
            print(f"  State: {state_str}")

            # Correct interpretation confirmed through hardware testing
            return {
                "disk_available": state_str[STATE_BIT_DISK_AVAILABLE] == "1",
                "disk_in_open_tray": state_str[STATE_BIT_DISK_IN_OPEN_TRAY] == "1",
                "disk_lifted": state_str[STATE_BIT_DISK_LIFTED] == "1",
                "tray_out": state_str[STATE_BIT_TRAY_OUT] == "1",
            }

        # No valid state string found
        print(f"Warning: Could not find valid state string in response: {response}")
        # Return safe defaults
        return {
            "disk_available": False,
            "disk_in_open_tray": False,
            "disk_lifted": False,
            "tray_out": False,
        }

    def disk_available(self) -> bool:
        """Check if a disk is available in the input queue.

        Returns:
            True if disk available
        """
        return self.get_state()["disk_available"]

    def open_tray(self) -> None:
        """Send command to open the tray.

        Note: Does not wait for tray to open. Caller must poll for state change.
        """
        self._open_tray_fn()

    def close_tray(self) -> None:
        """Send command to close the tray.

        Note: Does not wait for tray to close. Caller must poll for state change.
        """
        self._close_tray_fn()

    def reset_usb(self) -> bool:
        """Reset the USB device to clear any stuck states.

        This performs a USB-level reset which can help recover from:
        - E09 errors
        - USB timeout errors
        - Other communication issues

        Note: After reset, the device will be re-enumerated. Caller should
        poll for device availability before continuing operations.

        Returns:
            bool: True if reset successful, False otherwise
        """
        try:
            print("Performing USB reset...")
            self.dev.reset()
            print("USB reset completed")
            # Caller should poll for device availability after reset
            return True
        except Exception as e:
            print(f"USB reset failed: {e}")
            return False
