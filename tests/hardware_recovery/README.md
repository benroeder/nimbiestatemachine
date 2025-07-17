# Hardware Recovery Tests

These tests verify the robust startup procedure that handles disks stuck in the drive.

## Background

The Nimbie hardware has a limitation: it cannot detect if a disk is present in a closed drive. This can lead to disks being "stuck" if the system crashes or loses power while a disk is loaded.

Additionally, we discovered the hardware can get into inconsistent states where:
- The dropper mechanism is already holding a disk
- Hardware sensors report incorrect state
- Dropper mechanism is in an error state

## Solution

The state machine now includes a robust startup procedure that:
1. First checks if the dropper is already holding a disk and clears it
2. Checks if the tray is closed during initialization
3. Opens the tray if closed
4. Always attempts to lift any disk that might be present (even if not detected)
5. Properly disposes of any found disk

## Test Scripts

### 1. `recover_dropper.py`
Recovers the dropper mechanism from error states. Use this if you get AT+S03 (dropper error) messages.

```bash
python tests/hardware_recovery/recover_dropper.py
```

### 2. `setup_disk_in_drive.py`
Places a disk in the drive and exits. This simulates a crash/power loss scenario with a disk loaded.

```bash
# Step 1: Place a disk in the drive
python tests/hardware_recovery/setup_disk_in_drive.py

# Step 2: Test the recovery by creating a new state machine
python -c "from nimbie import NimbieStateMachine; sm = NimbieStateMachine('1')"
```

### 3. `test_startup_recovery.py`
The most comprehensive test. It demonstrates the recovery process in a single session by:
- Placing a disk in the drive
- Calling `transition_to_idle()` to simulate recovery
- Showing the disk being detected and removed

```bash
python tests/hardware_recovery/test_startup_recovery.py
```

### 4. `check_dropper_state.py`
Checks if the dropper is already holding a disk and attempts to clear it. This helped us discover the edge case where the dropper can be holding a disk at startup.

```bash
python tests/hardware_recovery/check_dropper_state.py
```

### 5. `test_improved_startup.py`
Tests the improved startup procedure that handles both lifted disks and disks in closed drives.

```bash
python tests/hardware_recovery/test_improved_startup.py
```

### 6. `check_detailed_state.py`
Provides detailed hardware state information for debugging.

```bash
python tests/hardware_recovery/check_detailed_state.py
```

### 7. `force_disk_removal.py`
Attempts forced disk removal when hardware state is inconsistent.

```bash
python tests/hardware_recovery/force_disk_removal.py
```

### 8. `manual_disk_removal.py`
Manual disk removal with dropper reset attempts.

```bash
python tests/hardware_recovery/manual_disk_removal.py
```

### 9. `verify_clean_state.py`
Verifies the hardware is in a clean state after recovery.

```bash
python tests/hardware_recovery/verify_clean_state.py
```

### 10. `test_example_recovery.py`
Tests that the example_state_machine.py properly recovers from startup issues.

```bash
python tests/hardware_recovery/test_example_recovery.py
```

### 11. `test_lifted_disk_startup.py`
Specifically tests startup when the dropper is already holding a disk.

```bash
python tests/hardware_recovery/test_lifted_disk_startup.py
```

## Expected Behavior

When the state machine starts up, you should see:
```
2025-07-17 11:26:07,100 - Performing startup disk check...
2025-07-17 11:26:07,416 - Tray is closed at startup, checking for stuck disk
2025-07-17 11:26:07,416 - Opening tray
2025-07-17 11:26:08,344 - Tray opened successfully
2025-07-17 11:26:08,344 - Attempting to lift any disk that might be present
2025-07-17 11:26:09,544 - Found and removed stuck disk from previous session
```

## Hardware States

The hardware state is represented as an 8-bit string (e.g., `0100001xx`):
- Bit 1: Disk available in queue (1 = yes, 0 = no)
- Bit 3: Disk in open tray (1 = yes, 0 = no)
- Bit 4: Disk lifted by gripper (1 = yes, 0 = no)
- Bit 5: Tray out/open (1 = open, 0 = closed)

## Common Response Codes

- `AT+O`: Operation successful
- `AT+S03`: Dropper error (gripper issue)
- `AT+S07`: Successfully placed disk on tray
- `AT+S00`: No disk in tray to lift

## Testing Workflow

1. **Normal operation test**: Just create a state machine and process disks normally
2. **Crash recovery test**: Use `setup_disk_in_drive.py` to simulate a crash, then start a new instance
3. **Single session test**: Use `test_startup_recovery.py` to see the full recovery process