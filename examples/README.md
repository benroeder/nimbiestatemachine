# Nimbie Examples

This directory contains example scripts showing how to use the Nimbie State Machine for various disk processing tasks.

## Running Examples

All examples require the Nimbie hardware to be connected and powered on.

### First Time Setup
```bash
# From project root
make venv
source venv/bin/activate
make install-dev

# Or manually:
pip install -e .
```

### Running Examples
```bash
# From project root
python examples/example_simple.py

# Or from examples directory
cd examples
python example_simple.py
```

## Available Examples

### example_simple.py
The simplest possible example - processes a single disk with a basic verification function.

### example_state_machine.py
Complete demonstration of all state machine features including:
- Single disk processing
- Batch processing with progress tracking
- Manual mode for testing/recovery
- Error recovery demonstration
- Continuous processing mode

### example_disk_imaging.py
Practical example for automated disk imaging/backup showing:
- How to integrate with dd for disk imaging
- Progress reporting during imaging
- Error handling for read errors
- Batch processing of multiple disks

### example_polling_config.py
Demonstrates different polling configurations:
- Fast polling for responsive operations
- Slow polling to reduce CPU usage
- Custom timeouts for different operations

### example_logging_config.py
Shows how to configure logging:
- Reduce logging verbosity
- Log to file instead of console
- Custom log formatting
- Multiple log handlers

### test_queue_cycle.py
Simple queue processing demonstration with:
- Progress display
- Batch processing of multiple disks
- Interrupt handling

## Common Patterns

### Basic Disk Processing
```python
from nimbie import NimbieStateMachine

def process_disk():
    # Your disk processing logic here
    return True  # Accept disk

sm = NimbieStateMachine(target_drive="1")
processed, accepted = sm.process_one_disk(process_fn=process_disk)
```

### Monitoring State Transitions
All state transitions are automatically logged:
```
2025-07-17 10:25:15,496 - State transition: idle -> loading (trigger: start_load)
2025-07-17 10:25:15,496 - State transition: loading -> processing (trigger: complete_load)
2025-07-17 10:25:15,996 - State transition: processing -> unloading (trigger: start_unload)
2025-07-17 10:25:23,304 - State transition: unloading -> idle (trigger: complete_unload)
```

### Batch Processing
```python
stats = sm.process_batch(count=10, process_fn=process_disk)
print(f"Processed {stats['total']} disks")
```

### Continuous Processing
```python
# Process disks until interrupted
sm.process_continuous(process_fn=process_disk)
```

## Drive Configuration

Remember to specify the correct drive when initializing:
- macOS: Use drive index from `drutil list` (usually "1" or "2")
- Linux: Use device path like "/dev/sr0" or "/dev/cdrom"