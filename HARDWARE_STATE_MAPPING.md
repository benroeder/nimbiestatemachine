# Nimbie Hardware State Bit Mapping

## Confirmed State Bit Positions

Based on systematic hardware testing on macOS with Nimbie hardware:

### State String Format
The Nimbie returns state in format: `{xxxxxxxx}` where each `x` is a binary digit (0 or 1).

### Bit Position Mapping (0-indexed)

| Position | Name | Description | Confirmed |
|----------|------|-------------|-----------|
| 0 | Unknown | Purpose unknown | ? |
| 1 | disk_available | 1 when disks in input queue, 0 when empty | Yes |
| 2 | Unknown | Purpose unknown | ? |
| 3 | disk_in_open_tray | 1 when disk placed in open tray | Yes |
| 4 | disk_lifted | 1 when disk lifted by gripper | Yes |
| 5 | tray_out | 1 when tray open, 0 when closed | Yes |
| 6 | Unknown | Usually 1 | ? |
| 7+ | Unknown | Usually 'xx' | ? |

## Test Results

### Tray State Testing
- Initial (tray closed): `0000001xx` → bit 5 = 0 (confirmed)
- After open command: `0000011xx` → bit 5 = 1 (confirmed)
- After close command: `0000001xx` → bit 5 = 0 (confirmed)

### Disk Placement Testing
- Before place (tray open): `0100011xx`
- After place command: `0001011xx`
- Changed bits: 
  - Bit 1: 1→0 (disk removed from queue) (confirmed)
  - Bit 3: 0→1 (disk now in tray) (confirmed)

### Physical Observations
1. Place disk command (AT+S07) drops disk from queue into open tray
2. Disk is visible in tray after placement
3. Disk is NOT lifted after placement
4. Tray remains open after disk placement

## Command Response Codes
- `AT+S07`: Successfully placed disk on tray
- `AT+S10`: Tray in wrong state
- `AT+S03`: Dropper error
- `AT+S00`: No disk in tray
- `AT+S12`: Tray already has disk
- `AT+S14`: No disk in queue
- `AT+E09`: Unknown error (often requires hardware reset)
- `AT+O`: Operation success (lift/drop)

## Notes
- Hardware operations include built-in polling
- Physical operations take time to complete
- State should be polled after commands when needed