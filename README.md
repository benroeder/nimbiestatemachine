# nimbiestatemachine
Python driver for acronova's nimbie NB21

This project was inspired by the original [nimbie-py](https://github.com/mattsoulanille/nimbie-py) implementation.

## Features
- **Clean Architecture**: Separated hardware driver and state machine orchestration
- **Polling-Based**: Configurable polling intervals and timeouts, no hardcoded delays
- **Direct Hardware Control**: USB interface with immediate command execution
- **State Machine**: Safe, structured disk processing workflows with automatic error recovery
- **Batch Processing**: Support for multiple disks with queue management
- **Manual Mode**: Testing and recovery operations that bypass state restrictions
- **Comprehensive Error Handling**: USB reset, state reading retry, automatic recovery
- **Type Safety**: Full type hints and mypy compliance

## Installation

### For Development
```bash
# Clone the repository
git clone https://github.com/benroeder/nimbiestatemachine.git
cd nimbiestatemachine

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Install development dependencies
pip install -e ".[dev]"
```

### For Usage
```bash
# Install directly from GitHub
pip install git+https://github.com/benroeder/nimbiestatemachine.git

# Or install from PyPI (when published)
pip install nimbie
```

## Quick Start

### Basic Usage (Direct Hardware Control)
```python
from nimbie import NimbieDriver

# Initialize the hardware with target drive
# macOS: drive index (1, 2, etc.)
# Linux: device path ("/dev/sr0", "/dev/cdrom", etc.)
driver = NimbieDriver(target_drive="1")

# Get hardware state
state = driver.get_state()
print(f"Disk available: {state['disk_available']}")
print(f"Tray out: {state['tray_out']}")

# Send commands (returns immediately)
driver.open_tray()
driver.place_disk()
driver.close_tray()
driver.lift_disk()
driver.accept_disk()
```

### Using the State Machine (Recommended)
```python
from nimbie import NimbieStateMachine

# Initialize state machine with target drive and polling configuration
# macOS: drive index (1, 2, etc.)
# Linux: device path ("/dev/sr0", "/dev/cdrom", etc.)
sm = NimbieStateMachine(
    target_drive="1",
    poll_interval=0.1,  # Poll every 100ms
    default_timeout=10.0  # 10 second timeout
)

# Process a single disk
def process_disk():
    print("Processing disk...")
    # Your processing logic here
    return True  # Accept disk

processed, accepted = sm.process_one_disk(process_fn=process_disk)

# Process multiple disks
stats = sm.process_batch(count=3, process_fn=process_disk)
print(f"Processed {stats['total']} disks: {stats['accepted']} accepted, {stats['rejected']} rejected")

# Continuous processing
sm.process_continuous(process_fn=process_disk)
```

### Manual Mode (Testing and Recovery)
```python
# Use manual mode to bypass state restrictions
with sm.manual_operation():
    sm.manual_open_tray()
    sm.manual_place_disk()
    sm.manual_lift_disk()
    sm.manual_close_tray()
    sm.manual_accept_disk()
    
    # Force state transitions for testing
    sm.manual_set_state('processing')

# High-level operations with polling
sm.load_disk_from_queue()  # Complete disk loading workflow
sm.unload_disk_to_accept()  # Complete disk unloading workflow
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      SYSTEM ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Application Layer                                              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Your Code (process_disk function)                      │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                  │
│                              ▼                                  │
│  State Machine Layer        ┌──────────────────────┐            │
│  ┌───────────────────┐      │  High-Level APIs     │            │
│  │ NimbieStateMachine│◀─────│  • process_batch()   │            │
│  │                   │      │  • process_one_disk()│            │
│  │ • States          │      │  • load_disk_from_   │            │
│  │ • Transitions     │      │    queue()           │            │
│  │ • Polling Logic   │      └──────────────────────┘            │
│  │ • Error Recovery  │                                          │
│  └────────┬──────────┘                                          │
│           │ polls for state changes                             │
│           ▼                                                     │
│  Driver Layer              ┌──────────────────────┐             │
│  ┌──────────────────┐      │  Hardware Commands   │             │
│  │  NimbieDriver    │◀─────│  • place_disk()      │             │
│  │                  │      │  • lift_disk()       │             │
│  │ • USB Commands   │      │  • accept_disk()     │             │
│  │ • No Waiting     │      │  • open_tray()       │             │
│  │ • Returns Fast   │      │  • get_state()       │             │
│  └────────┬─────────┘      └──────────────────────┘             │
│           │                                                     │
│           ▼                                                     │
│  Hardware Layer                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Nimbie USB Device (VID: 0x1723, PID: 0x0945)           │    │
│  │  CD/DVD Drive (drutil on macOS, eject on Linux)         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Clean Driver Interface
- **nimbie.driver**: Pure hardware interface, commands only
- **No polling or waiting**: Returns immediately after sending commands
- **USB reset support**: Recovery from communication errors
- **State reading retry**: Handles inconsistent hardware responses

### State Machine with Polling
- **Configurable polling**: Adjustable intervals and timeouts
- **No hardcoded delays**: All timing via polling
- **Safe operation sequences**: `idle` → `loading` → `processing` → `unloading` → `idle`
- **Error recovery**: Automatic transitions to safe state
- **Manual mode**: Bypass state restrictions for testing/recovery

## Configuration

### Hardware Configuration
1. Specify the correct drive when initializing:
   - macOS: Use drive index (1, 2, etc.) from `drutil list`
   - Linux: Use device path ("/dev/sr0", "/dev/cdrom", etc.)
2. Ensure USB permissions are set correctly for the Nimbie device (VID: 0x1723, PID: 0x0945)

### Polling Configuration
```python
# Fast polling for responsive operations
sm = NimbieStateMachine(target_drive="1", poll_interval=0.05, default_timeout=10.0)

# Slower polling to reduce CPU usage
sm = NimbieStateMachine(target_drive="1", poll_interval=0.5, default_timeout=30.0)

# Note: Disk placement operations use 30s timeout by default due to mechanical timing
```

## Testing

```bash
# Run all tests
pytest

# Run only hardware tests
pytest -m hardware

# Run specific test
pytest tests/test_nimbie_state_machine.py::test_disk_loading_cycle -v
```

## Disk Processing Flow

```
┌─────────────────────────────────────────────────────────────┐
│                   DISK PROCESSING FLOW                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Input Queue     ┌─────┐ ┌─────┐ ┌─────┐                    │
│  (Disks waiting) │ CD3 │ │ CD2 │ │ CD1 │                    │
│                  └─────┘ └─────┘ └──┬──┘                    │
│                                     │                       │
│                        1. LOAD DISK │                       │
│                     ┌───────────────▼────────────┐          │
│                     │  • Open tray               │          │
│                     │  • Place disk from queue   │          │
│                     │  • Close tray              │          │
│                     └───────────────┬────────────┘          │
│                                     │                       │
│                       2. PROCESS    ▼                       │
│                     ┌────────────────────────────┐          │
│                     │  Your process_disk()       │          │
│                     │  function executes         │          │
│                     │  Returns: True or False    │          │
│                     └───────────────┬────────────┘          │
│                                     │                       │
│                      3. UNLOAD DISK │                       │
│                     ┌───────────────▼────────────┐          │
│                     │  • Open tray               │          │
│                     │  • Lift disk               │          │
│                     │  • Close tray              │          │
│                     │  • Drop to pile            │          │
│                     └──────┬─────────────┬───────┘          │
│                            │             │                  │
│                   if True  │             │ if False         │
│                            ▼             ▼                  │
│  Accept Pile        ┌─────────┐   ┌─────────┐  Reject Pile  │
│  (Good disks)       │  CD1    │   │  CD2    │ (Bad disks)   │
│                     └─────────┘   └─────────┘               │
│                                                             │
│                     Repeat for all disks                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Hardware State Mapping

See [HARDWARE_STATE_MAPPING.md](HARDWARE_STATE_MAPPING.md) for details on hardware state bits and their meanings.

## Examples

All examples are in the `examples/` directory:

- [examples/example_state_machine.py](examples/example_state_machine.py) - Complete example showing all state machine features
- [examples/example_disk_imaging.py](examples/example_disk_imaging.py) - Practical example for automated disk imaging/backup
- [examples/example_simple.py](examples/example_simple.py) - Simple disk processing example
- [examples/example_polling_config.py](examples/example_polling_config.py) - Polling configuration examples
- [examples/test_queue_cycle.py](examples/test_queue_cycle.py) - Queue processing demonstration

## API Documentation

See [STATE_MACHINE_API.md](STATE_MACHINE_API.md) for detailed API documentation and examples.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
