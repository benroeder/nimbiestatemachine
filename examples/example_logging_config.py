#!/usr/bin/env python3
"""
Example showing how to configure logging in the Nimbie State Machine.
"""

import logging

from nimbie import NimbieStateMachine


def main():
    """Demonstrate different logging configurations."""

    print("Nimbie Logging Configuration Examples")
    print("=" * 50)

    # Example 1: Default logging (INFO level to stdout)
    print("\n1. Default logging configuration:")
    print("-" * 30)
    _ = NimbieStateMachine(target_drive="1")
    print("Default: Logs all operations to stdout")

    # Example 2: Reduced logging (WARNING level)
    print("\n2. Reduced logging (WARNING level only):")
    print("-" * 30)
    _ = NimbieStateMachine(target_drive="1", log_level=logging.WARNING)
    print("Only warnings and errors will be logged")

    # Example 3: No logging (ERROR level only)
    print("\n3. Minimal logging (ERROR level only):")
    print("-" * 30)
    _ = NimbieStateMachine(target_drive="1", log_level=logging.ERROR)
    print("Only errors will be logged")

    # Example 4: Custom file handler
    print("\n4. Logging to file:")
    print("-" * 30)
    file_handler = logging.FileHandler("nimbie_operations.log")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )
    _ = NimbieStateMachine(target_drive="1", log_handler=file_handler)
    print("Logs will be written to nimbie_operations.log")

    # Example 5: Custom handler with different format
    print("\n5. Custom format logging:")
    print("-" * 30)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter(
            "[%(levelname)s] %(message)s"  # Simpler format without timestamp
        )
    )
    _ = NimbieStateMachine(target_drive="1", log_handler=console_handler)
    print("Logs will use custom format without timestamp")

    # Example 6: Multiple handlers (advanced)
    print("\n6. Advanced: Using Python's logging configuration:")
    print("-" * 30)

    # Configure the nimbie logger directly
    nimbie_logger = logging.getLogger("nimbie")
    nimbie_logger.handlers = []  # Clear existing handlers

    # Add both file and console handlers
    file_handler2 = logging.FileHandler("nimbie_debug.log")
    file_handler2.setLevel(logging.DEBUG)
    console_handler2 = logging.StreamHandler()
    console_handler2.setLevel(logging.INFO)

    nimbie_logger.addHandler(file_handler2)
    nimbie_logger.addHandler(console_handler2)
    nimbie_logger.setLevel(logging.DEBUG)

    # Create state machine (it will use the configured logger)
    _ = NimbieStateMachine(target_drive="1")
    print("Logs go to both console (INFO+) and file (DEBUG+)")

    print("\n" + "=" * 50)
    print("Logging configuration examples complete!")


if __name__ == "__main__":
    main()
