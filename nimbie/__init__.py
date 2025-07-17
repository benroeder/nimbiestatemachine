"""
Nimbie - Python driver for Acronova Nimbie NB21 CD/DVD duplicator.

This package provides a clean architecture for controlling Nimbie hardware:
- NimbieDriver: Low-level hardware interface (commands only)
- NimbieStateMachine: High-level state machine with polling and workflows
- NimbiePureStateMachine: Pure state machine pattern with all operations in transitions
"""

from .driver import NimbieDriver
from .state_machine import NimbieStateMachine
from .pure_state_machine import NimbiePureStateMachine

__version__ = "0.1.0"
__all__ = ["NimbieDriver", "NimbieStateMachine", "NimbiePureStateMachine"]
