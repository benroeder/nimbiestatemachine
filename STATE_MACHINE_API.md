# Nimbie State Machine API

## Overview

The `NimbieStateMachine` class provides a safe, structured way to control Nimbie hardware operations through well-defined states and transitions. It uses a clean driver interface with polling-based operations for reliable hardware control.

## Architecture

- **Clean Driver**: `nimbie_driver.py` provides immediate command execution
- **Polling-Based**: State machine polls hardware for state changes
- **Configurable**: Adjustable polling intervals and timeouts
- **No Hardcoded Delays**: All timing via polling, no `time.sleep()`

## States

The state machine has five states:

1. **idle** - No operation in progress, ready to start processing
2. **loading** - Loading disk from queue to drive
3. **processing** - Disk in drive, ready for operations
4. **unloading** - Removing disk from drive
5. **error** - Error state with automatic recovery

## State Transitions

```
┌─────────────────────────────────────────────────────────────┐
│                   NIMBIE STATE MACHINE                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│    ┌────────┐      ┌─────────┐      ┌────────────┐          │
│    │  IDLE  │      │ LOADING │      │ PROCESSING │          │
│    │        │      │         │      │            │          │
│    │ Ready  │─────▶│ Tray    │─────▶│   Disk in  │          │
│    │  for   │      │  opens, │      │   drive,   │          │
│    │  disk  │      │  places │      │   ready    │          │
│    └────────┘      │  disk   │      └──────┬─────┘          │
│         ▲          └────┬────┘             │                │
│         │               │                  │                │
│         │               ▼                  ▼                │
│         │          ┌────────┐       ┌────────────┐          │
│         │          │ ERROR  │       │ UNLOADING  │          │
│         │          │        │       │            │          │
│         │          │ Failed │       │ Tray opens,│          │
│         └──────────│  ops,  │◀──────│ lifts disk,│          │
│         recovery   │ retry  │       │ drops to   │          │
│                    └────────┘       │ accept/    │          │
│                         ▲           │ reject     │          │
│                         │           └────────────┘          │
│                         │                  │                │
│                         └──────────────────┘                │
│                          Any state can                      │
│                          transition to ERROR                │
│                                                             │
└─────────────────────────────────────────────────────────────┘

State Details:
- IDLE: No disk in drive, ready to load next disk
- LOADING: Opening tray, placing disk, closing tray
- PROCESSING: Disk loaded, user function executes
- UNLOADING: Opening tray, lifting disk, dropping to pile
- ERROR: Recovery mode, attempts to return to IDLE
```

## Public API

### Initialization

```python
from nimbie_state_machine import NimbieStateMachine

# Initialize with target drive
# macOS: drive index (1, 2, etc.)
# Linux: device path ("/dev/sr0", "/dev/cdrom", etc.)
sm = NimbieStateMachine(target_drive="1")

# Configure polling behavior
sm = NimbieStateMachine(
    target_drive="1",
    poll_interval=0.1,    # Poll every 100ms
    default_timeout=10.0  # 10 second timeout
)

# Use custom hardware instance
from nimbie_driver import NimbieDriver
driver = NimbieDriver(target_drive="1")
sm = NimbieStateMachine(target_drive="1", hardware=driver)
```

### Processing Disks

#### Single Disk Processing

```python
def my_process_function():
    """Process the disk contents."""
    # Your processing logic here
    # Return True to accept, False to reject
    return True

processed, accepted = sm.process_one_disk(process_fn=my_process_function)
```

#### Batch Processing

```python
# Process specific number of disks
stats = sm.process_batch(count=5, process_fn=my_process_function)

# Process all available disks
stats = sm.process_batch(process_fn=my_process_function)

# stats contains: {'total': N, 'accepted': X, 'rejected': Y}
```

#### Continuous Processing

```python
# Process disks continuously until queue is empty
sm.process_continuous(process_fn=my_process_function)

# Stop continuous processing
sm.stop_continuous()
```

### State-Aware Operations

These operations are only allowed in specific states:

```python
# Allowed in idle, loading, or unloading states
sm.open_tray()

# Allowed in any state (safety operation)
sm.close_tray()

# Only allowed in loading state
sm.place_disk()

# Only allowed in unloading state
sm.lift_disk()
sm.accept_disk()
sm.reject_disk()
```

### High-Level Operations

These operations combine multiple steps with polling:

```python
# Complete disk loading workflow
sm.load_disk_from_queue()
# Opens tray → places disk → closes tray → waits for completion

# Complete disk unloading to accept pile
sm.unload_disk_to_accept()
# Opens tray → lifts disk → closes tray → accepts disk

# Complete disk unloading to reject pile
sm.unload_disk_to_reject()
# Opens tray → lifts disk → closes tray → rejects disk
```

### Hardware State Access

```python
# Get current hardware state
state = sm.get_hardware_state()
# Returns: {
#     'disk_available': bool,
#     'tray_out': bool,
#     'disk_lifted': bool,
#     'disk_in_open_tray': bool
# }

# Get current state machine state
current_state = sm.state  # 'idle', 'loading', etc.

# Check specific conditions
if sm.hardware.disk_available():
    print("Disk ready to process")
```

## Manual Mode

Manual mode allows bypassing state restrictions for testing and recovery:

```python
# Use context manager for manual operations
with sm.manual_operation():
    # All manual operations available
    sm.manual_open_tray()
    sm.manual_close_tray()
    sm.manual_place_disk()
    sm.manual_lift_disk()
    sm.manual_accept_disk()
    sm.manual_reject_disk()
    
    # Force state transitions
    sm.manual_set_state('processing')
```

### Manual Mode Operations

- `manual_open_tray()` - Open the disk tray
- `manual_close_tray()` - Close the disk tray
- `manual_place_disk()` - Place disk from queue onto tray
- `manual_lift_disk()` - Lift disk from tray
- `manual_accept_disk()` - Drop lifted disk to accept pile
- `manual_reject_disk()` - Drop lifted disk to reject pile
- `manual_set_state(state)` - Force transition to specific state

## Error Handling

The state machine automatically handles errors:

1. Any operation error triggers transition to error state
2. Error state automatically attempts recovery
3. Recovery returns hardware to safe state (tray closed, no disk lifted)
4. State machine returns to idle after recovery

### USB Error Recovery

```python
# Automatic USB reset on communication errors
if not sm.hardware.reset_usb():
    print("USB reset failed, manual intervention required")

# State reading retry mechanism handles inconsistent responses
state = sm.get_hardware_state()  # Retries up to 3 times
```

## Example: Complete Disk Processing

```python
from nimbie_state_machine import NimbieStateMachine
import time

def verify_disk_content():
    """Simulate disk verification."""
    print("Reading disk content...")
    time.sleep(5)  # Simulate read time
    
    # Check disk content (example)
    disk_is_valid = True  # Your validation logic
    
    return disk_is_valid

# Initialize with target drive
sm = NimbieStateMachine(target_drive="1")

# Process all disks in queue
stats = sm.process_batch(process_fn=verify_disk_content)

print(f"Processing complete!")
print(f"Total disks: {stats['total']}")
print(f"Accepted: {stats['accepted']}")
print(f"Rejected: {stats['rejected']}")
```

## Example: Error Recovery

```python
# Manual recovery from unknown state
with sm.manual_operation():
    # Get current hardware state
    hw_state = sm.get_hardware_state()
    
    # Recover based on state
    if hw_state['disk_lifted']:
        # Drop the disk
        if hw_state['tray_out']:
            sm.manual_close_tray()
        sm.manual_accept_disk()
    
    # Ensure tray is closed
    if hw_state['tray_out']:
        sm.manual_close_tray()
    
    # Reset to idle state
    sm.manual_set_state('idle')
```

## Polling Configuration

### Polling Parameters

```python
# Fast polling for responsive operations
sm = NimbieStateMachine(poll_interval=0.05, default_timeout=10.0)

# Slower polling to reduce CPU usage
sm = NimbieStateMachine(poll_interval=0.5, default_timeout=30.0)

# Custom timeout for specific operations
sm.load_disk_from_queue(timeout=60.0)  # 60 second timeout
```

### Polling Method Template

```python
def wait_for_condition(self, condition_fn, timeout=None):
    """Poll until condition is met."""
    timeout = timeout or self.default_timeout
    
    if not self._poll_until(condition_fn, timeout):
        raise TimeoutError("Condition not met within timeout")
```

## Logging

The state machine logs all operations with timestamps:

```
2025-07-15 14:31:58,319 - State machine initialized in idle state
2025-07-15 14:31:59,271 - State: loading - Loading disk...
2025-07-15 14:31:59,271 - Opening tray
2025-07-15 14:32:01,991 - Placing disk from queue
2025-07-15 14:32:13,031 - Closing tray
2025-07-15 14:32:14,311 - State: processing - Disk loaded
```

## Thread Safety

The state machine is NOT thread-safe. Use appropriate synchronization if accessing from multiple threads.

## Performance Considerations

### Polling Optimization

- **Fast polling (0.05s)**: More responsive, higher CPU usage
- **Slow polling (0.5s)**: Less responsive, lower CPU usage
- **Default (0.1s)**: Good balance for most use cases

### USB Communication

- Commands execute immediately but hardware operations take time
- Typical timings:
  - Tray open/close: 2-3 seconds
  - Disk placement: 8-12 seconds
  - Disk lifting: 3-5 seconds
  - USB communication: ~0.3 seconds per command

### Error Recovery

- State reading retry: Up to 3 attempts with 100ms delay
- USB reset: 2 second delay for device re-enumeration
- Automatic recovery to safe state on any error