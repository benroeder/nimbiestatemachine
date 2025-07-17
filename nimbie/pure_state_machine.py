"""Pure state machine implementation for Nimbie hardware control.

This module implements a pure state machine pattern where all hardware
operations happen within state transitions, not as separate method calls.
"""

import logging
import time
from typing import Optional, Callable, Union, Any, Dict

from transitions.extensions import HierarchicalMachine

from .driver import NimbieDriver


class NimbiePureStateMachine:
    """Pure state machine implementation for Nimbie hardware."""
    
    # Define states with hierarchical loading state
    states = [
        {
            'name': 'initializing',
            'children': [
                'checking_hardware',      # Initial hardware check
                'clearing_lifted_disk',   # Clear any disk lifted by dropper
                'checking_tray_state',    # Check if tray is open or closed
                'clearing_open_tray',     # Clear disk from open tray if present
                'closing_empty_tray',     # Close empty tray
                'checking_closed_drive',  # Check for disk in closed drive
                'initialization_complete' # Ready to transition to ready state
            ],
            'initial': 'checking_hardware'
        },
        'ready',         # Ready for operations (replaces 'idle')
        {
            'name': 'loading',
            'children': [
                'opening_tray',
                'waiting_tray_open',
                'placing_disk',
                'waiting_disk_placed',
                'closing_tray',
                'waiting_tray_closed'
            ],
            'initial': 'opening_tray'
        },
        'processing',    # Disk in drive
        {
            'name': 'unloading',
            'children': [
                'opening_tray',        # Opening tray to remove disk
                'waiting_tray_open',   # Waiting for tray to open
                'lifting_disk',        # Lifting disk from tray
                'waiting_disk_lifted', # Waiting for disk to be lifted
                'closing_tray',        # Closing tray before dropping
                'waiting_tray_closed', # Waiting for tray to close
                'dropping_disk',       # Dropping disk to accept/reject pile
                'final_ready'          # Final state before ready
            ],
            'initial': 'opening_tray'
        },
        'error'          # Error state
    ]
    
    def __init__(
        self,
        target_drive: Union[str, int],
        hardware: Optional[NimbieDriver] = None,
        poll_interval: float = 0.1,
        default_timeout: float = 30.0,
        log_level: Optional[int] = None,
    ):
        """Initialize the pure state machine.
        
        Args:
            target_drive: Drive identifier (required)
            hardware: Optional NimbieDriver instance
            poll_interval: Time between polls in seconds
            default_timeout: Default timeout for operations (30s for disk operations)
            log_level: Logging level (default: INFO)
        """
        # Set up logging
        self.logger = logging.getLogger("nimbie.pure")
        self.logger.setLevel(log_level if log_level is not None else logging.INFO)
        
        # Initialize hardware
        self.hardware = hardware if hardware else NimbieDriver(target_drive=target_drive)
        
        # Polling configuration
        self.poll_interval = poll_interval
        self.default_timeout = default_timeout
        
        # Initialize the hierarchical state machine
        self.machine = HierarchicalMachine(
            model=self,
            states=self.states,
            initial='initializing',
            send_event=True,  # Enables event data for error handling
            auto_transitions=False,  # We'll define all transitions explicitly
            ignore_invalid_triggers=True,  # Don't raise exception on invalid triggers
            model_override=False  # Allow binding our methods
        )
        
        # State attribute will be added by transitions
        self.state: str  # Type hint for the state attribute
        
        # Hardware state storage
        self.hardware_state: Dict[str, Any] = {}
        
        # Track whether we're accepting or rejecting
        self.accept_mode: bool = True
        
        # Add transitions
        self._add_transitions()
        
        # Add on_enter callbacks for initialization sub-states
        self.machine.on_enter_initializing_clearing_lifted_disk('_on_enter_clearing_lifted_disk')
        self.machine.on_enter_initializing_checking_tray_state('_on_enter_checking_tray_state')
        self.machine.on_enter_initializing_clearing_open_tray('_on_enter_clearing_open_tray')
        self.machine.on_enter_initializing_closing_empty_tray('_on_enter_closing_empty_tray')
        self.machine.on_enter_initializing_checking_closed_drive('_on_enter_checking_closed_drive')
        self.machine.on_enter_initializing_initialization_complete('_on_enter_initialization_complete')
        
        # Add on_enter callbacks for loading sub-states
        self.machine.on_enter_loading_opening_tray('_on_enter_opening_tray')
        self.machine.on_enter_loading_placing_disk('_on_enter_placing_disk')
        self.machine.on_enter_loading_closing_tray('_on_enter_closing_tray')
        
        # Add on_enter callbacks for unloading sub-states
        self.machine.on_enter_unloading_opening_tray('_on_enter_unloading_opening_tray')
        self.machine.on_enter_unloading_waiting_tray_open('_start_unload_tray_open_polling')
        self.machine.on_enter_unloading_lifting_disk('_on_enter_lifting_disk')
        self.machine.on_enter_unloading_waiting_disk_lifted('_start_disk_lifted_polling')
        self.machine.on_enter_unloading_closing_tray('_on_enter_unloading_closing_tray')
        self.machine.on_enter_unloading_waiting_tray_closed('_start_unload_tray_closed_polling')
        self.machine.on_enter_unloading_dropping_disk('_on_enter_dropping_disk')
        self.machine.on_enter_unloading_final_ready('_on_enter_final_ready')
        
        self.logger.info(f"NimbiePureStateMachine initialized in state: {self.state}")
    
    def close(self) -> None:
        """Close the hardware connection and cleanup resources."""
        if hasattr(self, 'hardware') and self.hardware is not None:
            if hasattr(self.hardware, 'close'):
                self.hardware.close()
            self.hardware = None
            self.logger.info("Pure state machine closed")
    
    def __del__(self) -> None:
        """Cleanup when object is garbage collected."""
        self.close()
    
    def _add_transitions(self):
        """Define all state transitions."""
        # Initialization sub-state transitions
        # checking_hardware → clearing_lifted_disk
        self.machine.add_transition(
            trigger='hardware_checked',
            source='initializing_checking_hardware',
            dest='initializing_clearing_lifted_disk'
        )
        
        # clearing_lifted_disk → checking_tray_state
        self.machine.add_transition(
            trigger='lifted_disk_cleared',
            source='initializing_clearing_lifted_disk',
            dest='initializing_checking_tray_state'
        )
        
        # checking_tray_state → clearing_open_tray (if tray open)
        self.machine.add_transition(
            trigger='tray_is_open',
            source='initializing_checking_tray_state',
            dest='initializing_clearing_open_tray'
        )
        
        # checking_tray_state → checking_closed_drive (if tray closed)
        self.machine.add_transition(
            trigger='tray_is_closed',
            source='initializing_checking_tray_state',
            dest='initializing_checking_closed_drive'
        )
        
        # clearing_open_tray → closing_empty_tray
        self.machine.add_transition(
            trigger='open_tray_cleared',
            source='initializing_clearing_open_tray',
            dest='initializing_closing_empty_tray'
        )
        
        # closing_empty_tray → checking_closed_drive
        self.machine.add_transition(
            trigger='empty_tray_closed',
            source='initializing_closing_empty_tray',
            dest='initializing_checking_closed_drive'
        )
        
        # checking_closed_drive → initialization_complete
        self.machine.add_transition(
            trigger='closed_drive_checked',
            source='initializing_checking_closed_drive',
            dest='initializing_initialization_complete'
        )
        
        # initialization_complete → ready
        self.machine.add_transition(
            trigger='initialization_done',
            source='initializing_initialization_complete',
            dest='ready',
            after='_log_ready'
        )
        
        # Initialize trigger starts the process
        self.machine.add_transition(
            trigger='initialize',
            source='initializing',
            dest='initializing_checking_hardware',
            after='_check_hardware'
        )
        
        # Load disk transition: ready → loading_opening_tray
        self.machine.add_transition(
            trigger='load_disk',
            source='ready',
            dest='loading_opening_tray',
            conditions=['_can_load_disk'],
            before='_prepare_loading',
            after=['_start_loading', '_log_loading']
        )
        
        # Loading sub-state transitions
        # opening_tray → waiting_tray_open (automatic after opening command)
        self.machine.add_transition(
            trigger='tray_opening',
            source='loading_opening_tray',
            dest='loading_waiting_tray_open',
            after=['_log_waiting_tray_open', '_start_tray_open_polling']
        )
        
        # waiting_tray_open → placing_disk (when tray is open)
        self.machine.add_transition(
            trigger='tray_opened',
            source='loading_waiting_tray_open',
            dest='loading_placing_disk',
            before='_place_disk',
            after='_log_placing_disk'
        )
        
        # placing_disk → waiting_disk_placed (automatic after place command)
        self.machine.add_transition(
            trigger='disk_placing',
            source='loading_placing_disk',
            dest='loading_waiting_disk_placed',
            after=['_log_waiting_disk_placed', '_start_disk_placed_polling']
        )
        
        # waiting_disk_placed → closing_tray (when disk is placed)
        self.machine.add_transition(
            trigger='disk_placed',
            source='loading_waiting_disk_placed',
            dest='loading_closing_tray',
            before='_close_tray',
            after='_log_closing_tray'
        )
        
        # closing_tray → waiting_tray_closed (automatic after close command)
        self.machine.add_transition(
            trigger='tray_closing',
            source='loading_closing_tray',
            dest='loading_waiting_tray_closed',
            after=['_log_waiting_tray_closed', '_start_tray_closed_polling']
        )
        
        # waiting_tray_closed → processing (when tray is closed)
        self.machine.add_transition(
            trigger='tray_closed',
            source='loading_waiting_tray_closed',
            dest='processing',
            after='_log_processing'
        )
        
        # Accept disk transition: processing → unloading
        self.machine.add_transition(
            trigger='accept_disk',
            source='processing',
            dest='unloading_opening_tray',
            before='_prepare_accept'
        )
        
        # Reject disk transition: processing → unloading (same states, different mode)
        self.machine.add_transition(
            trigger='reject_disk',
            source='processing',
            dest='unloading_opening_tray',
            before='_prepare_reject'
        )
        
        # Unloading sub-state transitions
        # opening_tray → waiting_tray_open
        self.machine.add_transition(
            trigger='unload_tray_opening',
            source='unloading_opening_tray',
            dest='unloading_waiting_tray_open'
        )
        
        # waiting_tray_open → lifting_disk (when tray is open)
        self.machine.add_transition(
            trigger='unload_tray_opened',
            source='unloading_waiting_tray_open',
            dest='unloading_lifting_disk'
        )
        
        # lifting_disk → waiting_disk_lifted
        self.machine.add_transition(
            trigger='disk_lifting',
            source='unloading_lifting_disk',
            dest='unloading_waiting_disk_lifted'
        )
        
        # waiting_disk_lifted → closing_tray (when disk is lifted)
        self.machine.add_transition(
            trigger='disk_lifted',
            source='unloading_waiting_disk_lifted',
            dest='unloading_closing_tray'
        )
        
        # closing_tray → waiting_tray_closed
        self.machine.add_transition(
            trigger='unload_tray_closing',
            source='unloading_closing_tray',
            dest='unloading_waiting_tray_closed'
        )
        
        # waiting_tray_closed → dropping_disk (when tray is closed)
        self.machine.add_transition(
            trigger='unload_tray_closed',
            source='unloading_waiting_tray_closed',
            dest='unloading_dropping_disk'
        )
        
        # dropping_disk → final_ready (after drop)
        self.machine.add_transition(
            trigger='disk_dropped',
            source='unloading_dropping_disk',
            dest='unloading_final_ready'
        )
        
        # final_ready → ready (final transition)
        self.machine.add_transition(
            trigger='unload_complete',
            source='unloading_final_ready',
            dest='ready',
            after='_log_ready'
        )
        
        # Error transitions - can go to error from any state
        self.machine.add_transition(
            trigger='to_error',
            source='*',  # From any state
            dest='error',
            after='_log_error'
        )
        
        # Recovery transition - error → ready
        self.machine.add_transition(
            trigger='recover',
            source='error',
            dest='ready',
            before='_check_hardware_recovery',
            after='_log_recovery'
        )
    
    def _check_hardware(self, event_data: Optional[Any] = None) -> None:
        """Check hardware during initialization."""
        self.logger.info("Checking hardware during initialization...")
        try:
            state = self.hardware.get_state()
            self.logger.info(f"Hardware state during init: {state}")
            self.hardware_state = state  # Store for use in other methods
            # Transition to next step
            self.hardware_checked()
        except Exception as e:
            self.logger.error(f"Hardware check failed: {e}")
            self.to_error()
            raise
    
    # Initialization state callbacks
    def _on_enter_clearing_lifted_disk(self, event_data: Optional[Any] = None) -> None:
        """Check and clear any disk lifted by dropper."""
        self.logger.info("Checking for lifted disk...")
        if self.hardware_state.get('disk_lifted', False):
            self.logger.info("Found lifted disk, clearing it...")
            # First ensure tray is closed
            if self.hardware_state.get('tray_out', False):
                self.logger.info("Closing tray before dropping disk...")
                self.hardware.close_tray()
                # Wait for tray to close
                time.sleep(3)
            # Drop the disk
            self.hardware.reject_disk()
            self.logger.info("Dropped lifted disk to reject pile")
        else:
            self.logger.info("No lifted disk found")
        self.lifted_disk_cleared()
    
    def _on_enter_checking_tray_state(self, event_data: Optional[Any] = None) -> None:
        """Check if tray is open or closed."""
        # Get fresh state
        self.hardware_state = self.hardware.get_state()
        if self.hardware_state.get('tray_out', False):
            self.logger.info("Tray is open")
            self.tray_is_open()
        else:
            self.logger.info("Tray is closed")
            self.tray_is_closed()
    
    def _on_enter_clearing_open_tray(self, event_data: Optional[Any] = None) -> None:
        """Clear any disk from open tray."""
        self.logger.info("Checking for disk in open tray...")
        if self.hardware_state.get('disk_in_open_tray', False):
            self.logger.info("Found disk in tray, attempting to lift it...")
            try:
                self.hardware.lift_disk()
                # Close tray before dropping the disk
                self.hardware.close_tray()
                # Wait for tray to close
                if self._wait_for_condition(
                    lambda: not self.hardware.get_state().get('tray_out', False),
                    timeout=45.0,
                    name='tray close before reject'
                ):
                    # Drop the disk
                    self.hardware.reject_disk()
                    self.logger.info("Cleared disk from tray to reject pile")
                else:
                    self.logger.error("Tray failed to close before reject")
                    self.to_error()
                    return
            except Exception as e:
                self.logger.warning(f"Could not lift disk from tray: {e}")
                self.logger.info("Trying alternative approach: close tray with disk")
                # Alternative approach: close tray with disk in it
                # This puts the disk in the drive, then we can try to lift it
                self.hardware.close_tray()
                # Wait for tray to close
                if self._wait_for_condition(
                    lambda: not self.hardware.get_state().get('tray_out', False),
                    timeout=45.0,
                    name='tray close with disk'
                ):
                    # Now try to lift the disk from the closed drive
                    try:
                        self.hardware.lift_disk()
                        # Drop the disk
                        self.hardware.reject_disk()
                        self.logger.info("Cleared disk from drive to reject pile")
                    except Exception as e2:
                        self.logger.error(f"Could not lift disk from drive: {e2}")
                        self.to_error()
                        return
                else:
                    self.logger.error("Tray failed to close with disk")
                    self.to_error()
                    return
        else:
            self.logger.info("No disk in open tray")
        self.open_tray_cleared()
    
    def _on_enter_closing_empty_tray(self, event_data: Optional[Any] = None) -> None:
        """Close the empty tray."""
        self.logger.info("Closing empty tray...")
        self.hardware.close_tray()
        # Wait for tray to close
        if self._wait_for_condition(
            lambda: not self.hardware.get_state().get('tray_out', False),
            timeout=45.0,
            name='tray close'
        ):
            self.empty_tray_closed()
        else:
            self.logger.error("Timeout waiting for tray to close")
            self.to_error()
    
    def _on_enter_checking_closed_drive(self, event_data: Optional[Any] = None) -> None:
        """Check for disk in closed drive (lift attempt)."""
        self.logger.info("Checking for disk in closed drive...")
        # Hardware limitation: can't detect disk in closed drive
        # So we always try to lift
        try:
            self.hardware.lift_disk()
            # If lift succeeds, drop it
            self.hardware.reject_disk()
            self.logger.info("Found and cleared disk from closed drive")
        except Exception as e:
            # Check if the error is because tray needs to be open
            if "opposite state" in str(e).lower():
                self.logger.info("Disk detected in closed drive, opening tray to remove it...")
                # Open tray to access the disk
                self.hardware.open_tray()
                # Wait for tray to open
                if self._wait_for_condition(
                    lambda: self.hardware.get_state().get('tray_out', False),
                    timeout=30.0,
                    name='tray open for disk removal'
                ):
                    # Now try to lift the disk
                    try:
                        self.hardware.lift_disk()
                        # Close tray before dropping
                        self.hardware.close_tray()
                        # Wait for tray to close
                        if self._wait_for_condition(
                            lambda: not self.hardware.get_state().get('tray_out', False),
                            timeout=45.0,
                            name='tray close before reject'
                        ):
                            # Drop the disk
                            self.hardware.reject_disk()
                            self.logger.info("Successfully removed disk from drive")
                        else:
                            self.logger.error("Tray failed to close after disk removal")
                            self.to_error()
                            return
                    except Exception as e2:
                        # If lift fails because there's no disk, that's OK
                        if "no disk" in str(e2).lower():
                            self.logger.info("No disk in drive after opening tray")
                            # Close the tray since it's empty
                            self.hardware.close_tray()
                            # Wait for tray to close
                            self._wait_for_condition(
                                lambda: not self.hardware.get_state().get('tray_out', False),
                                timeout=45.0,
                                name='tray close after empty check'
                            )
                        else:
                            self.logger.error(f"Failed to remove disk from drive: {e2}")
                            self.to_error()
                            return
                else:
                    self.logger.error("Tray failed to open for disk removal")
                    self.to_error()
                    return
            else:
                self.logger.info("No disk in closed drive (lift failed as expected)")
        self.closed_drive_checked()
    
    def _on_enter_initialization_complete(self, event_data: Optional[Any] = None) -> None:
        """Initialization is complete, ready to transition."""
        self.logger.info("Hardware initialization complete")
        self.initialization_done()
    
    def _log_ready(self, event_data: Optional[Any] = None) -> None:
        """Log when ready state is reached."""
        self.logger.info("State machine is now ready for operations")
    
    def _log_error(self, event_data: Optional[Any] = None) -> None:
        """Log when error state is reached."""
        self.logger.error("State machine entered error state")
    
    def _check_hardware_recovery(self, event_data: Optional[Any] = None) -> None:
        """Check hardware during recovery from error state."""
        self.logger.info("Checking hardware during recovery from error state...")
        try:
            state = self.hardware.get_state()
            self.logger.info(f"Hardware state during recovery: {state}")
            self.hardware_state = state  # Store for use in other methods
        except Exception as e:
            self.logger.error(f"Hardware check failed during recovery: {e}")
            # Stay in error state
            self.to_error()
            raise
    
    def _log_recovery(self, event_data: Optional[Any] = None) -> None:
        """Log when recovery to ready state is complete."""
        self.logger.info("State machine recovered from error state to ready")
    
    def _can_load_disk(self, event_data: Optional[Any] = None) -> bool:
        """Check if disk is available to load."""
        can_load = self.hardware.disk_available()
        self.logger.info(f"Checking if can load disk: {can_load}")
        if not can_load:
            self.logger.warning("Cannot load disk - no disk available in queue")
        return can_load
    
    def _prepare_loading(self, event_data: Optional[Any] = None) -> None:
        """Prepare for loading (runs before state transition)."""
        self.logger.info("Preparing to load disk...")
    
    def _start_loading(self, event_data: Optional[Any] = None) -> None:
        """Start the loading process (runs after state transition)."""
        self.logger.info("Starting disk loading process...")
    
    def _log_loading(self, event_data: Optional[Any] = None) -> None:
        """Log when loading state is reached."""
        self.logger.info("State machine entered loading state")
    
    # Loading sub-state callbacks
    def _log_waiting_tray_open(self, event_data: Optional[Any] = None) -> None:
        """Log when waiting for tray to open."""
        self.logger.info("Waiting for tray to open...")
    
    # On-enter callbacks for loading sub-states
    def _on_enter_opening_tray(self, event_data: Optional[Any] = None) -> None:
        """Called when entering opening_tray state."""
        self.logger.info("Opening tray...")
        self.hardware.open_tray()
        # Transition to waiting state
        self.tray_opening()
    
    def _on_enter_placing_disk(self, event_data: Optional[Any] = None) -> None:
        """Called when entering placing_disk state."""
        self.logger.info("Placing disk on tray...")
        self.hardware.place_disk()
        # Transition to waiting state
        self.disk_placing()
    
    def _on_enter_closing_tray(self, event_data: Optional[Any] = None) -> None:
        """Called when entering closing_tray state."""
        self.logger.info("Closing tray...")
        self.hardware.close_tray()
        # Transition to waiting state
        self.tray_closing()
    
    def _place_disk(self, event_data: Optional[Any] = None) -> None:
        """Place disk on tray."""
        # This is now handled in _on_enter_placing_disk
        pass
    
    def _log_placing_disk(self, event_data: Optional[Any] = None) -> None:
        """Log when placing disk."""
        self.logger.info("Entered placing_disk state")
    
    def _log_waiting_disk_placed(self, event_data: Optional[Any] = None) -> None:
        """Log when waiting for disk placement."""
        self.logger.info("Waiting for disk to be placed...")
    
    def _close_tray(self, event_data: Optional[Any] = None) -> None:
        """Close the tray."""
        # This is now handled in _on_enter_closing_tray
        pass
    
    def _log_closing_tray(self, event_data: Optional[Any] = None) -> None:
        """Log when closing tray."""
        self.logger.info("Entered closing_tray state")
    
    def _log_waiting_tray_closed(self, event_data: Optional[Any] = None) -> None:
        """Log when waiting for tray to close."""
        self.logger.info("Waiting for tray to close...")
    
    def _log_processing(self, event_data: Optional[Any] = None) -> None:
        """Log when entering processing state."""
        self.logger.info("Disk loaded and ready for processing")
    
    # Polling methods - now using simple synchronous waiting
    def _start_tray_open_polling(self, event_data: Optional[Any] = None) -> None:
        """Wait for tray open status and trigger next state."""
        if self._wait_for_condition(
            lambda: self.hardware.get_state().get('tray_out', False),
            timeout=self.default_timeout,
            name='tray open'
        ):
            self.tray_opened()
        else:
            self.logger.error("Timeout waiting for tray to open")
            self.to_error()
    
    def _start_disk_placed_polling(self, event_data: Optional[Any] = None) -> None:
        """Wait for disk placed status and trigger next state."""
        if self._wait_for_condition(
            lambda: self.hardware.get_state().get('disk_in_open_tray', False),
            timeout=self.default_timeout,
            name='disk placed'
        ):
            self.disk_placed()
        else:
            self.logger.error("Timeout waiting for disk to be placed")
            self.to_error()
    
    def _start_tray_closed_polling(self, event_data: Optional[Any] = None) -> None:
        """Wait for tray closed status and trigger next state."""
        if self._wait_for_condition(
            lambda: not self.hardware.get_state().get('tray_out', False),
            timeout=45.0,  # Longer timeout for closing with disk
            name='tray closed'
        ):
            self.tray_closed()
        else:
            self.logger.error("Timeout waiting for tray to close")
            self.to_error()
    
    def _wait_for_condition(
        self,
        condition: Callable[[], bool],
        timeout: float,
        name: str
    ) -> bool:
        """Wait for a condition to become true.
        
        Args:
            condition: Function that returns True when condition is met
            timeout: Maximum time to wait
            name: Name for logging
            
        Returns:
            True if condition was met, False if timeout
        """
        start_time = time.time()
        self.logger.info(f"Waiting for {name} (timeout={timeout}s)")
        
        while time.time() - start_time < timeout:
            try:
                if condition():
                    self.logger.info(f"{name} condition met after {time.time() - start_time:.1f}s")
                    return True
                time.sleep(self.poll_interval)
            except Exception as e:
                self.logger.error(f"Error while waiting for {name}: {e}")
                return False
                
        return False
    
    # State query helpers
    def is_loading(self) -> bool:
        """Check if currently in any loading state."""
        return self.state.startswith('loading')
    
    def is_processing(self) -> bool:
        """Check if currently in processing state."""
        return self.state == 'processing'
    
    def is_ready(self) -> bool:
        """Check if currently in ready state."""
        return self.state == 'ready'
    
    def can_load_disk(self) -> bool:
        """Check if a disk can be loaded.
        
        Returns:
            True if in ready state and disk is available
        """
        return self.is_ready() and self.hardware.disk_available()
    
    # Clean API methods
    def load_next_disk(self) -> bool:
        """Load the next disk from the queue.
        
        Returns:
            True if disk loaded successfully, False otherwise
        """
        if self.state != 'ready':
            self.logger.warning(f"Cannot load disk from state '{self.state}' - must be in 'ready' state")
            return False
        
        if not self.hardware.disk_available():
            self.logger.warning("No disk available in queue")
            return False
            
        result = self.load_disk()
        if result and self.state == 'processing':
            self.logger.info("Disk loaded successfully")
            return True
        else:
            self.logger.error("Failed to load disk")
            return False
    
    def accept_current_disk(self) -> bool:
        """Accept the currently loaded disk.
        
        Returns:
            True if disk accepted successfully, False otherwise
        """
        if self.state != 'processing':
            self.logger.warning(f"Cannot accept disk from state '{self.state}' - must be in 'processing' state")
            return False
            
        result = self.accept_disk()
        if result and self.state == 'ready':
            self.logger.info("Disk accepted successfully")
            return True
        else:
            self.logger.error("Failed to accept disk")
            return False
    
    def reject_current_disk(self) -> bool:
        """Reject the currently loaded disk.
        
        Returns:
            True if disk rejected successfully, False otherwise
        """
        if self.state != 'processing':
            self.logger.warning(f"Cannot reject disk from state '{self.state}' - must be in 'processing' state")
            return False
            
        result = self.reject_disk()
        if result and self.state == 'ready':
            self.logger.info("Disk rejected successfully")
            return True
        else:
            self.logger.error("Failed to reject disk")
            return False
    
    # Unloading callbacks
    def _prepare_accept(self, event_data: Optional[Any] = None) -> None:
        """Prepare for accepting disk."""
        self.accept_mode = True
        self.logger.info("Preparing to accept disk")
    
    def _prepare_reject(self, event_data: Optional[Any] = None) -> None:
        """Prepare for rejecting disk."""
        self.accept_mode = False
        self.logger.info("Preparing to reject disk")
    
    def _on_enter_unloading_opening_tray(self, event_data: Optional[Any] = None) -> None:
        """Open tray to remove disk."""
        self.logger.info("Opening tray to unload disk...")
        self.hardware.open_tray()
        # Transition to waiting state
        self.unload_tray_opening()
    
    def _start_unload_tray_open_polling(self, event_data: Optional[Any] = None) -> None:
        """Wait for tray to open for unloading."""
        if self._wait_for_condition(
            lambda: self.hardware.get_state().get('tray_out', False),
            timeout=self.default_timeout,
            name='unload tray open'
        ):
            self.unload_tray_opened()
        else:
            self.logger.error("Timeout waiting for tray to open for unloading")
            self.to_error()
    
    def _on_enter_lifting_disk(self, event_data: Optional[Any] = None) -> None:
        """Lift disk from tray."""
        self.logger.info("Lifting disk from tray...")
        self.hardware.lift_disk()
        # Transition to waiting state
        self.disk_lifting()
    
    def _start_disk_lifted_polling(self, event_data: Optional[Any] = None) -> None:
        """Wait for disk to be lifted."""
        if self._wait_for_condition(
            lambda: self.hardware.get_state().get('disk_lifted', False),
            timeout=self.default_timeout,
            name='disk lifted'
        ):
            self.disk_lifted()
        else:
            self.logger.error("Timeout waiting for disk to be lifted")
            self.to_error()
    
    def _on_enter_dropping_disk(self, event_data: Optional[Any] = None) -> None:
        """Drop disk to accept or reject pile."""
        if self.accept_mode:
            self.logger.info("Dropping disk to accept pile...")
            self.hardware.accept_disk()
        else:
            self.logger.info("Dropping disk to reject pile...")
            self.hardware.reject_disk()
        # Transition to final ready state
        self.disk_dropped()
    
    def _on_enter_unloading_closing_tray(self, event_data: Optional[Any] = None) -> None:
        """Close empty tray after unloading."""
        self.logger.info("Closing empty tray after unloading...")
        self.hardware.close_tray()
        # Transition to waiting state
        self.unload_tray_closing()
    
    def _start_unload_tray_closed_polling(self, event_data: Optional[Any] = None) -> None:
        """Wait for tray to close after unloading."""
        if self._wait_for_condition(
            lambda: not self.hardware.get_state().get('tray_out', False),
            timeout=45.0,  # Longer timeout for closing
            name='unload tray closed'
        ):
            self.unload_tray_closed()
        else:
            self.logger.error("Timeout waiting for tray to close after unloading")
            self.to_error()
    
    def _on_enter_final_ready(self, event_data: Optional[Any] = None) -> None:
        """Handle final ready state before returning to ready."""
        self.logger.info("Unloading complete, returning to ready state")
        self.unload_complete()


# Allow running directly for testing
if __name__ == "__main__":
    print("Testing NimbiePureStateMachine imports...")
    sm = NimbiePureStateMachine(target_drive="1")
    print("Success! Imports working correctly.")