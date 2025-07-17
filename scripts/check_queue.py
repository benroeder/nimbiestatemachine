#!/usr/bin/env python3
"""Check if there are disks in the Nimbie queue."""

from nimbie import NimbieDriver

print("Checking disk queue...")
d = NimbieDriver('1')
state = d.get_state()

print(f"Hardware state: {state}")
print(f"Disk available: {state.get('disk_available', False)}")
print(f"Tray out: {state.get('tray_out', False)}")
print(f"Disk lifted: {state.get('disk_lifted', False)}")

if state.get('disk_available', False):
    print("✅ Disk available in queue - ready to load")
else:
    print("❌ No disk in queue - please add a disk to the Nimbie")
    print("   Add a disk to the input side of the Nimbie and run again")