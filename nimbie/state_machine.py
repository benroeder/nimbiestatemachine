"""Simple state machine for Nimbie hardware control."""

import logging
import sys
import time
from contextlib import contextmanager
from typing import Any, Callable, Optional, Union

from transitions import Machine

from .driver import NimbieDriver


class ImmediateStreamHandler(logging.StreamHandler):
    """Stream handler that flushes after each emit."""

    def emit(self, record: logging.LogRecord) -> None:
        super().emit(record)
        self.flush()


class NimbieStateMachine:
    """State machine to control Nimbie hardware operations."""

    # Define states
    states = [
        "idle",  # No operation in progress
        "loading",  # Loading disk from queue to drive
        "processing",  # Disk in drive, ready for operations
        "unloading",  # Removing disk from drive
        "error",  # Error state
    ]

    # Type hint for state attribute added by transitions
    state: str

    def __init__(
        self,
        target_drive: Union[str, int],
        hardware: Optional[NimbieDriver] = None,
        poll_interval: float = 0.1,
        default_timeout: float = 10.0,
    ) -> None:
        """Initialize state machine with hardware interface.

        Args:
            target_drive: Required drive specifier for multi-drive systems
                         - macOS: drive index (1,2,...) as integer or string
                         - Linux: device path ("/dev/sr0", "/dev/cdrom", etc.)
            hardware: Nimbie hardware instance (creates new one if None)
            poll_interval: Time between polling attempts in seconds (default 0.1)
            default_timeout: Default timeout for operations in seconds (default 10.0)
        """
        # Set up logging with immediate flush
        handler = ImmediateStreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))

        self.logger = logging.getLogger("nimbie")
        self.logger.setLevel(logging.INFO)
        self.logger.handlers = []  # Clear any existing handlers
        self.logger.addHandler(handler)
        self.logger.propagate = False  # Don't propagate to root logger

        # Initialize hardware
        if hardware is None:
            self.hardware = NimbieDriver(target_drive=target_drive)
        else:
            self.hardware = hardware

        # Polling configuration
        self.poll_interval = poll_interval
        self.default_timeout = default_timeout

        # Initialize state machine
        self.machine = Machine(
            model=self, states=self.states, initial="idle", auto_transitions=False
        )

        # Define transitions
        self._add_transitions()

        # Manual mode for testing
        self.manual_mode = False

        self.logger.info("State machine initialized in idle state")

    def _add_transitions(self) -> None:
        """Define state transitions."""
        # From idle, we can start loading
        self.machine.add_transition(
            trigger="start_load",
            source="idle",
            dest="loading",
            conditions=["can_load_disk"],
            after=lambda: self._log_transition("start_load", "idle", "loading"),
        )

        # From loading to processing (disk loaded)
        self.machine.add_transition(
            trigger="complete_load",
            source="loading",
            dest="processing",
            after=lambda: self._log_transition("complete_load", "loading", "processing"),
        )

        # From processing to unloading
        self.machine.add_transition(
            trigger="start_unload",
            source="processing",
            dest="unloading",
            after=lambda: self._log_transition("start_unload", "processing", "unloading"),
        )

        # From unloading back to idle
        self.machine.add_transition(
            trigger="complete_unload",
            source="unloading",
            dest="idle",
            after=lambda: self._log_transition("complete_unload", "unloading", "idle"),
        )

        # Error transitions - can go to error from any state
        self.machine.add_transition(
            trigger="error_occurred",
            source=["idle", "loading", "processing", "unloading"],
            dest="error",
            before=lambda: setattr(self, '_error_source', self.state),
            after=lambda: self._log_transition("error_occurred", getattr(self, '_error_source', 'unknown'), "error"),
        )

        # Recovery from error
        self.machine.add_transition(
            trigger="recover",
            source="error",
            dest="idle",
            after=["reset_hardware", lambda: self._log_transition("recover", "error", "idle")],
        )

    # Type annotations for dynamically created transition methods
    def start_load(self) -> bool:  # type: ignore[empty-body]
        """Start loading a disk. Added by transitions library."""
        pass  # This method is dynamically created by transitions library

    def complete_load(self) -> bool:  # type: ignore[empty-body]
        """Complete loading a disk. Added by transitions library."""
        pass  # This method is dynamically created by transitions library

    def start_unload(self) -> bool:  # type: ignore[empty-body]
        """Start unloading a disk. Added by transitions library."""
        pass  # This method is dynamically created by transitions library

    def complete_unload(self) -> bool:  # type: ignore[empty-body]
        """Complete unloading a disk. Added by transitions library."""
        pass  # This method is dynamically created by transitions library

    def error_occurred(self) -> bool:  # type: ignore[empty-body]
        """Transition to error state. Added by transitions library."""
        pass  # This method is dynamically created by transitions library

    def recover(self) -> bool:  # type: ignore[empty-body]
        """Recover from error state. Added by transitions library."""
        pass  # This method is dynamically created by transitions library

    def can_load_disk(self) -> bool:
        """Check if we can load a disk."""
        return self.hardware.disk_available()

    def _log_transition(self, trigger: str, source: str, dest: str) -> None:
        """Log state transitions for debugging."""
        self.logger.info(f"State transition: {source} -> {dest} (trigger: {trigger})")

    def reset_hardware(self) -> None:
        """Reset hardware to safe state."""
        self.logger.info("Resetting hardware to safe state")
        try:
            state = self.hardware.get_state()

            # If disk is lifted, drop it
            if state["disk_lifted"]:
                if state["tray_out"]:
                    self._close_tray()
                self._accept_disk()

            # Ensure tray is closed
            if state["tray_out"]:
                self._close_tray()
        except Exception as e:
            self.logger.error(f"Error during hardware reset: {e}")
            # Continue anyway - hardware might be in timeout state

    def transition_to_idle(self) -> None:
        """Transition hardware to idle state from any current state."""
        self.logger.info("Transitioning to idle state")
        try:
            state = self.hardware.get_state()

            # Handle lifted disk
            if state["disk_lifted"]:
                self.logger.info("Disk is lifted, dropping it")
                if state["tray_out"]:
                    self._close_tray()
                self._accept_disk()

            # Handle disk in open tray (was loaded in drive)
            elif state["disk_in_open_tray"] and state["tray_out"]:
                self.logger.info("Disk in open tray, removing it")
                self._lift_disk()
                self._close_tray()
                self._accept_disk()

            # Handle closed tray (might have disk loaded)
            elif not state["tray_out"]:
                self.logger.info("Tray closed, checking for loaded disk")
                self._open_tray()
                import time

                time.sleep(1)
                state = self.hardware.get_state()
                if state["disk_in_open_tray"]:
                    self.logger.info("Found disk in drive, removing it")
                    self._lift_disk()
                    self._close_tray()
                    self._accept_disk()
                else:
                    self._close_tray()

            # Force state machine to idle using proper API
            self.machine.set_state("idle")
            self.logger.info("Hardware transitioned to idle state")

        except Exception as e:
            self.logger.error(f"Error transitioning to idle: {e}")
            # Don't call error_occurred if we're already in error state
            if self.state != "error":
                self.error_occurred()
            raise

    def handle_timeout_error(self) -> bool:
        """Handle USB timeout errors by attempting hardware recovery."""
        self.logger.warning("USB timeout detected, attempting hardware recovery")

        # Force state machine to error state using proper API
        self.machine.set_state("error")

        # Try basic recovery operations without reading state
        try:
            self.logger.info("Attempting basic hardware recovery operations")

            # Try to close tray (blind operation)
            try:
                self.hardware.close_tray()
                self.logger.info("Sent close tray command")
            except Exception:
                pass

            # Try to accept any lifted disk (blind operation)
            try:
                self.hardware.accept_disk()
                self.logger.info("Sent accept disk command")
            except Exception:
                pass

            # Wait for hardware to settle
            import time

            time.sleep(2)

            # Try to read state again
            try:
                state = self.hardware.get_state()
                self.logger.info(f"Hardware recovery successful, state: {state}")
                self.machine.set_state("idle")
                return True
            except Exception as e:
                self.logger.error(f"Hardware still not responding after recovery: {e}")
                return False

        except Exception as e:
            self.logger.error(f"Hardware recovery failed: {e}")
            return False

    def get_hardware_state(self) -> dict[str, bool]:
        """Get current hardware state."""
        try:
            return self.hardware.get_state()
        except Exception as e:
            self.logger.error(f"Error getting hardware state: {e}")
            self.error_occurred()
            raise

    @contextmanager
    def manual_operation(self) -> Any:
        """Context manager to enable manual mode for testing.

        When in manual mode, normally-private operations can be accessed
        through their manual_* counterparts.

        Example:
            with sm.manual_operation():
                sm.manual_open_tray()
                sm.manual_place_disk()
        """
        self.manual_mode = True
        self.logger.info("Entering manual mode for testing")
        try:
            yield self
        finally:
            self.manual_mode = False
            self.logger.info("Exiting manual mode")

    def _open_tray(self) -> None:
        """Internal method to open the disk tray."""
        self.logger.info("Opening tray")
        # Send command to open tray
        self.hardware.open_tray()
        # Wait for tray to actually open
        if not self.wait_for_tray_open():
            raise TimeoutError("Tray failed to open within timeout")

    def open_tray(self) -> None:
        """Open the disk tray."""
        # Allow in idle, loading, or unloading states
        if self.state not in ["idle", "loading", "unloading"]:
            raise RuntimeError(f"Cannot open tray in {self.state} state")
        self._open_tray()

    def _close_tray(self) -> None:
        """Internal method to close the disk tray."""
        self.logger.info("Closing tray")
        # Send command to close tray
        self.hardware.close_tray()
        # Wait for tray to actually close
        if not self.wait_for_tray_close():
            raise TimeoutError("Tray failed to close within timeout")

    def close_tray(self) -> None:
        """Close the disk tray."""
        # Allow in any state (safety operation)
        self._close_tray()

    def _place_disk(self) -> str:
        """Internal method to place a disk from the queue onto the tray."""
        self.logger.info("Placing disk from queue")

        # Check if disk is already in tray before placing
        state = self.hardware.get_state()
        if state["disk_in_open_tray"]:
            self.logger.info("Disk already in tray, skipping place operation")
            return "Already placed"

        # Send command to place disk
        result = self.hardware.place_disk()
        # Wait for disk to actually be placed (use longer timeout for mechanical operation)
        if not self.wait_for_disk_placed(timeout=30.0):
            raise TimeoutError("Disk failed to be placed within timeout")
        return result

    def place_disk(self) -> str:
        """Place a disk from the queue onto the tray."""
        # Only allow in loading state
        if self.state != "loading":
            raise RuntimeError(
                f"Cannot place disk in {self.state} state - must be in loading state"
            )
        return self._place_disk()

    def _lift_disk(self) -> str:
        """Internal method to lift the disk from the tray."""
        self.logger.info("Lifting disk from tray")
        # Send command to lift disk
        result = self.hardware.lift_disk()
        # Wait for disk to actually be lifted
        if not self.wait_for_disk_lifted():
            raise TimeoutError("Disk failed to be lifted within timeout")
        return result

    def lift_disk(self) -> str:
        """Lift the disk from the tray."""
        # Only allow in unloading state
        if self.state != "unloading":
            raise RuntimeError(
                f"Cannot lift disk in {self.state} state - must be in unloading state"
            )
        return self._lift_disk()

    def _accept_disk(self) -> str:
        """Internal method to accept the current disk (drop to accept pile)."""
        self.logger.info("Accepting disk")
        # Send command to accept disk
        result = self.hardware.accept_disk()
        # Wait for disk to actually be dropped
        if not self.wait_for_disk_dropped():
            raise TimeoutError("Disk failed to be dropped within timeout")
        return result

    def accept_disk(self) -> str:
        """Accept the current disk (drop to accept pile)."""
        # Only allow in unloading state
        if self.state != "unloading":
            raise RuntimeError(
                f"Cannot accept disk in {self.state} state - must be in unloading state"
            )
        return self._accept_disk()

    def _reject_disk(self) -> str:
        """Internal method to reject the current disk (drop to reject pile)."""
        self.logger.info("Rejecting disk")
        # Send command to reject disk
        result = self.hardware.reject_disk()
        # Wait for disk to actually be dropped
        if not self.wait_for_disk_dropped():
            raise TimeoutError("Disk failed to be dropped within timeout")
        return result

    def reject_disk(self) -> str:
        """Reject the current disk (drop to reject pile)."""
        # Only allow in unloading state
        if self.state != "unloading":
            raise RuntimeError(
                f"Cannot reject disk in {self.state} state - must be in unloading state"
            )
        return self._reject_disk()

    # Manual mode methods for testing
    def manual_open_tray(self) -> None:
        """Manually open tray (only in manual mode)."""
        if not self.manual_mode:
            raise RuntimeError("Manual operations only allowed in manual mode")
        self.logger.info("Manual: Opening tray")
        self._open_tray()

    def manual_close_tray(self) -> None:
        """Manually close tray (only in manual mode)."""
        if not self.manual_mode:
            raise RuntimeError("Manual operations only allowed in manual mode")
        self.logger.info("Manual: Closing tray")
        self._close_tray()

    def manual_place_disk(self) -> str:
        """Manually place disk (only in manual mode)."""
        if not self.manual_mode:
            raise RuntimeError("Manual operations only allowed in manual mode")
        self.logger.info("Manual: Placing disk")
        return self._place_disk()

    def manual_lift_disk(self) -> str:
        """Manually lift disk (only in manual mode)."""
        if not self.manual_mode:
            raise RuntimeError("Manual operations only allowed in manual mode")
        self.logger.info("Manual: Lifting disk")
        return self._lift_disk()

    def manual_accept_disk(self) -> str:
        """Manually accept disk (only in manual mode)."""
        if not self.manual_mode:
            raise RuntimeError("Manual operations only allowed in manual mode")
        self.logger.info("Manual: Accepting disk")
        return self._accept_disk()

    def manual_reject_disk(self) -> str:
        """Manually reject disk (only in manual mode)."""
        if not self.manual_mode:
            raise RuntimeError("Manual operations only allowed in manual mode")
        self.logger.info("Manual: Rejecting disk")
        return self._reject_disk()

    def manual_set_state(self, state: str) -> None:
        """Manually set state (only in manual mode)."""
        if not self.manual_mode:
            raise RuntimeError("Manual operations only allowed in manual mode")
        if state not in self.states:
            raise ValueError(f"Invalid state: {state}")
        self.logger.info(f"Manual: Setting state to {state}")
        # Force state transition without conditions
        self.machine.set_state(state)

    def process_one_disk(
        self, process_fn: Optional[Callable[[], bool]] = None
    ) -> tuple[bool, bool]:
        """Process a single disk through the complete cycle.

        Args:
            process_fn: Optional function to process disk contents.
                       Should return True to accept, False to reject.
                       If None, accepts all disks.

        Returns:
            tuple: (processed, accepted) - processed is True if disk was processed,
                   accepted is True if disk was accepted, False if rejected
        """
        try:
            # Must be in idle state to start
            if self.state != "idle":
                self.logger.warning(
                    f"Cannot process disk - not in idle state (current: {self.state})"
                )
                return False, False

            # Check if disk available
            if not self.hardware.disk_available():
                self.logger.info("No disk available to process")
                return False, False

            # Start loading sequence
            self.start_load()  # Transition: idle -> loading

            # Load disk
            self._open_tray()
            self._place_disk()
            self._close_tray()

            # Complete loading
            self.complete_load()  # Transition: loading -> processing

            # Process disk (user function)
            if process_fn:
                self.logger.info("Processing disk contents...")
                result = process_fn()
            else:
                result = True  # Default: accept all

            # Start unloading
            self.start_unload()  # Transition: processing -> unloading

            # Unload disk
            self._open_tray()
            self._lift_disk()
            self._close_tray()

            # Accept or reject based on result
            if result:
                self._accept_disk()
                self.logger.info("Disk accepted")
            else:
                self._reject_disk()
                self.logger.info("Disk rejected")

            # Complete unloading
            self.complete_unload()  # Transition: unloading -> idle

            return True, result

        except Exception as e:
            self.logger.error(f"Error processing disk: {e}")
            self.error_occurred()  # Transition: any -> error
            # Try to recover
            self.recover()  # Transition: error -> idle
            return False, False

    def process_batch(
        self,
        count: Optional[int] = None,
        process_fn: Optional[Callable[[], bool]] = None,
    ) -> dict[str, int]:
        """Process multiple disks in sequence.

        Args:
            count: Number of disks to process. If None, process all available.
            process_fn: Optional function to process each disk.

        Returns:
            dict: Statistics about the batch (total, accepted, rejected)
        """
        stats = {"total": 0, "accepted": 0, "rejected": 0}

        self.logger.info(f"Starting batch processing (count={count or 'all'})")

        while True:
            # Check count limit
            if count and stats["total"] >= count:
                break

            # Process one disk
            processed, accepted = self.process_one_disk(process_fn)
            if not processed:
                # No more disks available
                break

            stats["total"] += 1
            if accepted:
                stats["accepted"] += 1
            else:
                stats["rejected"] += 1

        self.logger.info(f"Batch complete: {stats}")
        return stats

    def process_continuous(
        self,
        process_fn: Optional[Callable[[], bool]] = None,
        check_interval: float = 1.0,
    ) -> dict[str, int]:
        """Process disks continuously until stopped.

        This method processes disks in a loop, checking for new disks
        at regular intervals. It's designed for continuous operation
        where disks are added to the queue while processing.

        Args:
            process_fn: Optional function to process each disk.
                       Should return True to accept, False to reject.
            check_interval: Time to wait between checks when queue is empty (seconds)

        Returns:
            dict: Statistics about the batch (total, accepted, rejected)

        Note:
            Call stop_continuous() from another thread to stop processing.
        """
        self._continuous_running = True
        stats = {"total": 0, "accepted": 0, "rejected": 0}

        self.logger.info("Starting continuous processing")

        try:
            while self._continuous_running:
                # Check if disk available
                if not self.hardware.disk_available():
                    self.logger.debug(f"No disk available, waiting {check_interval}s")
                    # Use polling interval for checking
                    time.sleep(check_interval)
                    continue

                # Process one disk
                processed, accepted = self.process_one_disk(process_fn)
                if processed:
                    stats["total"] += 1
                    if accepted:
                        stats["accepted"] += 1
                    else:
                        stats["rejected"] += 1
                    self.logger.info(
                        f"Processed disk {stats['total']}: {'accepted' if accepted else 'rejected'}"
                    )

        except KeyboardInterrupt:
            self.logger.info("Continuous processing interrupted by user")
        except Exception as e:
            self.logger.error(f"Error in continuous processing: {e}")
            self.error_occurred()
        finally:
            self._continuous_running = False
            self.logger.info(f"Continuous processing complete: {stats}")

        return stats

    def stop_continuous(self) -> None:
        """Stop continuous processing.

        This can be called from another thread to gracefully stop
        the process_continuous() method.
        """
        self.logger.info("Stopping continuous processing...")
        self._continuous_running = False

    # Polling infrastructure

    def _poll_until(
        self,
        condition: Callable[[], bool],
        timeout: Optional[float] = None,
        error_msg: Optional[str] = None,
    ) -> bool:
        """Poll until a condition is met or timeout occurs.

        Args:
            condition: Function that returns True when condition is met
            timeout: Timeout in seconds (uses default_timeout if None)
            error_msg: Optional error message for logging

        Returns:
            True if condition was met, False if timeout occurred
        """
        timeout = timeout or self.default_timeout
        start_time = time.time()

        while True:
            try:
                if condition():
                    return True
            except Exception as e:
                # Log errors but continue polling
                if error_msg:
                    self.logger.debug(f"{error_msg}: {e}")
                else:
                    self.logger.debug(f"Error during polling: {e}")

            # Check timeout
            if time.time() - start_time > timeout:
                if error_msg:
                    self.logger.warning(f"Polling timeout: {error_msg}")
                return False

            # Wait before next poll
            time.sleep(self.poll_interval)

    # Tray polling methods

    def wait_for_tray_open(self, timeout: Optional[float] = None) -> bool:
        """Poll until tray is open.

        Args:
            timeout: Timeout in seconds (uses default_timeout if None)

        Returns:
            True if tray opened, False if timeout

        Raises:
            TimeoutError: If timeout occurs (when used by state transitions)
        """
        self.logger.info("Waiting for tray to open...")

        def is_tray_open() -> bool:
            state = self.hardware.get_state()
            return state["tray_out"]

        success = self._poll_until(is_tray_open, timeout, "waiting for tray open")

        if success:
            self.logger.info("Tray opened successfully")
        else:
            self.logger.error("Timeout waiting for tray to open")

        return success

    def wait_for_tray_close(self, timeout: Optional[float] = None) -> bool:
        """Poll until tray is closed.

        Args:
            timeout: Timeout in seconds (uses default_timeout if None)

        Returns:
            True if tray closed, False if timeout

        Raises:
            TimeoutError: If timeout occurs (when used by state transitions)
        """
        self.logger.info("Waiting for tray to close...")

        def is_tray_closed() -> bool:
            state = self.hardware.get_state()
            return not state["tray_out"]

        success = self._poll_until(is_tray_closed, timeout, "waiting for tray close")

        if success:
            self.logger.info("Tray closed successfully")
        else:
            self.logger.error("Timeout waiting for tray to close")

        return success

    # Disk operation polling methods

    def wait_for_disk_placed(self, timeout: Optional[float] = None) -> bool:
        """Poll until disk is placed in open tray.

        Args:
            timeout: Timeout in seconds (uses default_timeout if None)

        Returns:
            True if disk placed, False if timeout
        """
        self.logger.info("Waiting for disk to be placed in tray...")

        def is_disk_in_tray() -> bool:
            state = self.hardware.get_state()
            return state["disk_in_open_tray"]

        success = self._poll_until(
            is_disk_in_tray, timeout, "waiting for disk placement"
        )

        if success:
            self.logger.info("Disk placed in tray successfully")
        else:
            self.logger.error("Timeout waiting for disk placement")

        return success

    def wait_for_disk_lifted(self, timeout: Optional[float] = None) -> bool:
        """Poll until disk is lifted by gripper.

        Args:
            timeout: Timeout in seconds (uses default_timeout if None)

        Returns:
            True if disk lifted, False if timeout
        """
        self.logger.info("Waiting for disk to be lifted...")

        def is_disk_lifted() -> bool:
            state = self.hardware.get_state()
            return state["disk_lifted"]

        success = self._poll_until(is_disk_lifted, timeout, "waiting for disk lift")

        if success:
            self.logger.info("Disk lifted successfully")
        else:
            self.logger.error("Timeout waiting for disk to be lifted")

        return success

    def wait_for_disk_dropped(self, timeout: Optional[float] = None) -> bool:
        """Poll until lifted disk is dropped (no longer lifted).

        Args:
            timeout: Timeout in seconds (uses default_timeout if None)

        Returns:
            True if disk dropped, False if timeout
        """
        self.logger.info("Waiting for disk to be dropped...")

        def is_disk_dropped() -> bool:
            state = self.hardware.get_state()
            return not state["disk_lifted"]

        success = self._poll_until(is_disk_dropped, timeout, "waiting for disk drop")

        if success:
            self.logger.info("Disk dropped successfully")
        else:
            self.logger.error("Timeout waiting for disk to be dropped")

        return success

    def wait_for_disk_in_drive(self, timeout: Optional[float] = None) -> bool:
        """Poll until disk is loaded in drive (tray closed with disk).

        This waits for the disk to be fully loaded, which means:
        - Tray is closed (not out)
        - Disk is not in open tray
        - Disk is not lifted

        Args:
            timeout: Timeout in seconds (uses default_timeout if None)

        Returns:
            True if disk loaded in drive, False if timeout
        """
        self.logger.info("Waiting for disk to be loaded in drive...")

        def is_disk_in_drive() -> bool:
            state = self.hardware.get_state()
            # Disk is in drive when tray is closed and disk is not visible
            return (
                not state["tray_out"]
                and not state["disk_in_open_tray"]
                and not state["disk_lifted"]
            )

        success = self._poll_until(
            is_disk_in_drive, timeout, "waiting for disk in drive"
        )

        if success:
            self.logger.info("Disk loaded in drive successfully")
        else:
            self.logger.error("Timeout waiting for disk to load in drive")

        return success

    # High-level operations

    def load_disk_from_queue(self) -> bool:
        """Load a disk from the queue into the drive.

        This is a complete operation that:
        1. Opens the tray
        2. Places a disk from the queue
        3. Closes the tray to load the disk

        Returns:
            True if disk was loaded successfully, False otherwise

        Raises:
            RuntimeError: If not in idle or loading state
        """
        # Must be in idle or loading state
        if self.state not in ["idle", "loading"]:
            raise RuntimeError(
                f"Cannot load disk in {self.state} state - must be in idle or loading state"
            )

        try:
            # Transition to loading if in idle
            if self.state == "idle":
                if not self.can_load_disk():
                    self.logger.warning("No disk available to load")
                    return False
                self.start_load()

            # Open tray
            self._open_tray()

            # Place disk from queue
            self._place_disk()

            # Close tray to load disk
            self._close_tray()

            # Wait for disk to be loaded in drive
            if not self.wait_for_disk_in_drive():
                raise TimeoutError("Disk failed to load in drive")

            # Transition to processing
            self.complete_load()

            self.logger.info("Disk loaded successfully from queue")
            return True

        except Exception as e:
            self.logger.error(f"Failed to load disk from queue: {e}")
            self.error_occurred()
            return False

    def unload_disk_to_accept(self) -> bool:
        """Unload the current disk and place it in the accept pile.

        This is a complete operation that:
        1. Opens the tray
        2. Lifts the disk from the tray
        3. Closes the tray
        4. Drops the disk to the accept pile

        Returns:
            True if disk was unloaded successfully, False otherwise

        Raises:
            RuntimeError: If not in processing or unloading state
        """
        # Must be in processing or unloading state
        if self.state not in ["processing", "unloading"]:
            raise RuntimeError(
                f"Cannot unload disk in {self.state} state - must be in processing or unloading state"
            )

        try:
            # Transition to unloading if in processing
            if self.state == "processing":
                self.start_unload()

            # Open tray
            self._open_tray()

            # Lift disk from tray
            self._lift_disk()

            # Close tray
            self._close_tray()

            # Accept disk
            self._accept_disk()

            # Transition to idle
            self.complete_unload()

            self.logger.info("Disk unloaded to accept pile")
            return True

        except Exception as e:
            self.logger.error(f"Failed to unload disk to accept: {e}")
            self.error_occurred()
            return False

    def unload_disk_to_reject(self) -> bool:
        """Unload the current disk and place it in the reject pile.

        This is a complete operation that:
        1. Opens the tray
        2. Lifts the disk from the tray
        3. Closes the tray
        4. Drops the disk to the reject pile

        Returns:
            True if disk was unloaded successfully, False otherwise

        Raises:
            RuntimeError: If not in processing or unloading state
        """
        # Must be in processing or unloading state
        if self.state not in ["processing", "unloading"]:
            raise RuntimeError(
                f"Cannot unload disk in {self.state} state - must be in processing or unloading state"
            )

        try:
            # Transition to unloading if in processing
            if self.state == "processing":
                self.start_unload()

            # Open tray
            self._open_tray()

            # Lift disk from tray
            self._lift_disk()

            # Close tray
            self._close_tray()

            # Reject disk
            self._reject_disk()

            # Transition to idle
            self.complete_unload()

            self.logger.info("Disk unloaded to reject pile")
            return True

        except Exception as e:
            self.logger.error(f"Failed to unload disk to reject: {e}")
            self.error_occurred()
            return False
