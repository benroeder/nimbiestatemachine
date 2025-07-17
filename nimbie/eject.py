import platform
import subprocess
from typing import Union


def open_tray(drive: Union[str, int], timeout: float = 10.0) -> None:
    """Open the CD/DVD tray using platform-specific commands.

    Args:
        drive: Required drive specifier
               - macOS: drive index (1,2,...) as integer or string
               - Linux: device path ("/dev/sr0", "/dev/cdrom", etc.)
        timeout: Timeout in seconds (default: 10.0)
    """
    if "Darwin" in platform.system():
        cmd = ["drutil", "-drive", str(drive), "tray", "eject"]
        result = subprocess.run(cmd, timeout=timeout)
    else:
        cmd = ["eject", str(drive)]
        result = subprocess.run(cmd, timeout=timeout)

    if result.returncode != 0:
        raise Exception(f"Failed to open tray for drive {drive}")


def close_tray(drive: Union[str, int], timeout: float = 30.0) -> None:
    """Close the CD/DVD tray using platform-specific commands.

    Args:
        drive: Required drive specifier
               - macOS: drive index (1,2,...) as integer or string
               - Linux: device path ("/dev/sr0", "/dev/cdrom", etc.)
        timeout: Timeout in seconds (default: 30.0 - longer for disk loading)
    """
    if "Darwin" in platform.system():
        cmd = ["drutil", "-drive", str(drive), "tray", "close"]
        result = subprocess.run(cmd, timeout=timeout)
    else:
        cmd = ["eject", "-t", str(drive)]
        result = subprocess.run(cmd, timeout=timeout)

    if result.returncode != 0:
        raise Exception(f"Failed to close tray for drive {drive}")


if __name__ == "__main__":
    import sys
    from time import sleep

    print(f"Platform: {platform.system()}")
    print("Testing tray control...")

    # Drive must be specified
    if len(sys.argv) < 2 or sys.argv[1] == "--auto":
        print("Error: Drive must be specified")
        print("Usage: python eject.py <drive> [--auto]")
        print("  macOS: python eject.py 1")
        print("  Linux: python eject.py /dev/sr0")
        sys.exit(1)

    drive = sys.argv[1]
    print(f"Using drive: {drive}")

    print("Opening tray...")
    open_tray(drive)

    if "--auto" in sys.argv:
        print("Waiting 3 seconds...")
        sleep(3)
    else:
        input("Press Enter to close tray...")

    print("Closing tray...")
    close_tray(drive)

    print("Test complete!")
