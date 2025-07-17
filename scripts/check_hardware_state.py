#!/usr/bin/env python3
"""Check current hardware state."""

from nimbie import NimbieDriver

print("Checking current hardware state...")
d = NimbieDriver('1')
state = d.get_state()

print("\nHardware state:")
for key, value in state.items():
    print(f"  {key}: {value}")
    
if state.get('tray_out'):
    print("\n⚠️ Tray is currently open")
    if state.get('disk_in_open_tray'):
        print("⚠️ Disk is in the open tray")