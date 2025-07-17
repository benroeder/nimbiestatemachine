#!/usr/bin/env python3
"""Close the tray to reset hardware state."""

from nimbie import NimbieDriver

print("Closing tray to reset hardware state...")
d = NimbieDriver('1')
d.close_tray()
print("Tray closed.")