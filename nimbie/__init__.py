"""
Nimbie - Python driver for Acronova Nimbie NB21 CD/DVD duplicator.

This package provides a clean architecture for controlling Nimbie hardware:
- NimbieDriver: Low-level hardware interface (commands only)
- NimbieStateMachine: High-level state machine with polling and workflows
"""

from .driver import NimbieDriver
from .state_machine import NimbieStateMachine

__version__ = "0.1.0"
__all__ = ["NimbieDriver", "NimbieStateMachine"]
