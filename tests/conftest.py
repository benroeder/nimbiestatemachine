"""Pytest configuration and fixtures for Nimbie tests."""

from collections.abc import Generator

import pytest

from nimbie import NimbieDriver, NimbieStateMachine


@pytest.fixture(scope="module")
def nimbie_hardware() -> Generator[NimbieDriver, None, None]:
    """Provide a shared Nimbie hardware instance for all tests in the module."""
    try:
        # Use drive 1 for tests (Nimbie drive)
        nimbie = NimbieDriver(target_drive="1")
        yield nimbie
    except Exception as e:
        pytest.skip(f"Hardware not available: {e}")


@pytest.fixture(scope="module")
def nimbie_state_machine(nimbie_hardware: NimbieDriver) -> NimbieStateMachine:
    """Provide a shared state machine instance for all tests in the module."""
    # Pass target_drive even though we're using existing hardware
    return NimbieStateMachine(target_drive="1", hardware=nimbie_hardware)


@pytest.fixture(autouse=True)
def ensure_clean_state(
    nimbie_state_machine: NimbieStateMachine,
) -> Generator[None, None, None]:
    """Ensure hardware is in a clean state before and after each test using state machine."""
    # Setup: transition to idle state before test
    try:
        print("\n[Setup] Transitioning to idle state...")
        nimbie_state_machine.transition_to_idle()
        print(f"[Setup] State machine in {nimbie_state_machine.state} state")
        print("[Setup] Hardware ready for test")
    except Exception as e:
        print(f"[Setup] Warning: Could not transition to idle: {e}")
        # Try USB timeout recovery
        if "Operation timed out" in str(e):
            print("[Setup] USB timeout detected, attempting recovery...")
            if nimbie_state_machine.handle_timeout_error():
                print("[Setup] Hardware recovery successful")
            else:
                print("[Setup] Hardware recovery failed")
        else:
            # Try normal recovery
            try:
                if nimbie_state_machine.state != "error":
                    nimbie_state_machine.error_occurred()
                nimbie_state_machine.recover()
                print("[Setup] Recovery successful")
            except Exception as recover_e:
                print(f"[Setup] Recovery failed: {recover_e}")

    # Run the test
    yield

    # Teardown: transition back to idle state after test
    try:
        print("\n[Teardown] Transitioning to idle state...")
        nimbie_state_machine.transition_to_idle()
        print(f"[Teardown] State machine in {nimbie_state_machine.state} state")
        print("[Teardown] Cleanup complete")
    except Exception as e:
        print(f"[Teardown] Error during cleanup: {e}")
        # Try USB timeout recovery
        if "Operation timed out" in str(e):
            print("[Teardown] USB timeout detected, attempting recovery...")
            if nimbie_state_machine.handle_timeout_error():
                print("[Teardown] Hardware recovery successful")
            else:
                print("[Teardown] Hardware recovery failed")
        else:
            # Try normal recovery
            try:
                if nimbie_state_machine.state != "error":
                    nimbie_state_machine.error_occurred()
                nimbie_state_machine.recover()
                print("[Teardown] Recovery successful")
            except Exception as recover_e:
                print(f"[Teardown] Recovery failed: {recover_e}")
