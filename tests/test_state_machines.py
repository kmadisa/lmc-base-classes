"""
This module contains the tests for the ska.base.state_machine module.
"""
import pytest

from ska.base.state_machine import BaseDeviceStateMachine, ObservationStateMachine
from .conftest import TransitionsStateMachineTester


device_state_machine_dag = [
    ("UNINITIALISED", "init_started", "INIT_ENABLED"),
    ("INIT_ENABLED", "to_notfitted", "INIT_DISABLED"),
    ("INIT_ENABLED", "to_offline", "INIT_DISABLED"),
    ("INIT_ENABLED", "to_online", "INIT_ENABLED"),
    ("INIT_ENABLED", "to_maintenance", "INIT_ENABLED"),
    ("INIT_ENABLED", "init_succeeded", "OFF"),
    ("INIT_ENABLED", "init_failed", "FAULT_ENABLED"),
    ("INIT_ENABLED", "fatal_error", "FAULT_ENABLED"),
    ("INIT_DISABLED", "to_notfitted", "INIT_DISABLED"),
    ("INIT_DISABLED", "to_offline", "INIT_DISABLED"),
    ("INIT_DISABLED", "to_online", "INIT_ENABLED"),
    ("INIT_DISABLED", "to_maintenance", "INIT_ENABLED"),
    ("INIT_DISABLED", "init_succeeded", "DISABLED"),
    ("INIT_DISABLED", "init_failed", "FAULT_DISABLED"),
    ("INIT_DISABLED", "fatal_error", "FAULT_DISABLED"),
    ("FAULT_DISABLED", "to_notfitted", "FAULT_DISABLED"),
    ("FAULT_DISABLED", "to_offline", "FAULT_DISABLED"),
    ("FAULT_DISABLED", "to_online", "FAULT_ENABLED"),
    ("FAULT_DISABLED", "to_maintenance", "FAULT_ENABLED"),
    ("FAULT_DISABLED", "reset_succeeded", "DISABLED"),
    ("FAULT_DISABLED", "reset_failed", "FAULT_DISABLED"),
    ("FAULT_DISABLED", "fatal_error", "FAULT_DISABLED"),
    ("FAULT_ENABLED", "to_notfitted", "FAULT_DISABLED"),
    ("FAULT_ENABLED", "to_offline", "FAULT_DISABLED"),
    ("FAULT_ENABLED", "to_online", "FAULT_ENABLED"),
    ("FAULT_ENABLED", "to_maintenance", "FAULT_ENABLED"),
    ("FAULT_ENABLED", "reset_succeeded", "OFF"),
    ("FAULT_ENABLED", "reset_failed", "FAULT_ENABLED"),
    ("FAULT_ENABLED", "fatal_error", "FAULT_ENABLED"),
    ("DISABLED", "to_notfitted", "DISABLED"),
    ("DISABLED", "to_offline", "DISABLED"),
    ("DISABLED", "to_online", "OFF"),
    ("DISABLED", "to_maintenance", "OFF"),
    ("DISABLED", "fatal_error", "FAULT_DISABLED"),
    ("OFF", "to_notfitted", "DISABLED"),
    ("OFF", "to_offline", "DISABLED"),
    ("OFF", "to_online", "OFF"),
    ("OFF", "to_maintenance", "OFF"),
    ("OFF", "on_succeeded", "ON"),
    ("OFF", "on_failed", "FAULT_ENABLED"),
    ("OFF", "fatal_error", "FAULT_ENABLED"),
    ("ON", "off_succeeded", "OFF"),
    ("ON", "off_failed", "FAULT_ENABLED"),
    ("ON", "fatal_error", "FAULT_ENABLED"),
]


@pytest.mark.state_machine_tester(device_state_machine_dag)
class BaseDeviceStateMachineTester(TransitionsStateMachineTester):
    """
    This class contains the test for the ska.low.mccs.state module.
    """
    @pytest.fixture
    def machine(self):
        """
        Fixture that returns the state machine under test in this class
        """
        yield BaseDeviceStateMachine()


observation_state_machine_dag = [
    ("EMPTY", "assign_started", "RESOURCING"),
    ("EMPTY", "fatal_error", "FAULT"),
    ("RESOURCING", "resourcing_succeeded_some_resources", "IDLE"),
    ("RESOURCING", "resourcing_succeeded_no_resources", "EMPTY"),
    ("RESOURCING", "resourcing_failed", "FAULT"),
    ("RESOURCING", "fatal_error", "FAULT"),
    ("IDLE", "assign_started", "RESOURCING"),
    ("IDLE", "release_started", "RESOURCING"),
    ("IDLE", "configure_started", "CONFIGURING"),
    ("IDLE", "abort_started", "ABORTING"),
    ("IDLE", "fatal_error", "FAULT"),
    ("CONFIGURING", "configure_succeeded", "READY"),
    ("CONFIGURING", "configure_failed", "FAULT"),
    ("CONFIGURING", "abort_started", "ABORTING"),
    ("CONFIGURING", "fatal_error", "FAULT"),
    ("READY", "end_succeeded", "IDLE"),
    ("READY", "end_failed", "FAULT"),
    ("READY", "configure_started", "CONFIGURING"),
    ("READY", "abort_started", "ABORTING"),
    ("READY", "scan_started", "SCANNING"),
    ("READY", "fatal_error", "FAULT"),
    ("SCANNING", "scan_succeeded", "READY"),
    ("SCANNING", "scan_failed", "FAULT"),
    ("SCANNING", "end_scan_succeeded", "READY"),
    ("SCANNING", "end_scan_failed", "FAULT"),
    ("SCANNING", "abort_started", "ABORTING"),
    ("SCANNING", "fatal_error", "FAULT"),
    ("ABORTING", "abort_succeeded", "ABORTED"),
    ("ABORTING", "abort_failed", "FAULT"),
    ("ABORTING", "fatal_error", "FAULT"),
    ("ABORTED", "obs_reset_started", "RESETTING"),
    ("ABORTED", "restart_started", "RESTARTING"),
    ("ABORTED", "fatal_error", "FAULT"),
    ("FAULT", "obs_reset_started", "RESETTING"),
    ("FAULT", "restart_started", "RESTARTING"),
    ("FAULT", "fatal_error", "FAULT"),
    ("RESETTING", "obs_reset_succeeded", "IDLE"),
    ("RESETTING", "obs_reset_failed", "FAULT"),
    ("RESETTING", "fatal_error", "FAULT"),
    ("RESTARTING", "restart_succeeded", "EMPTY"),
    ("RESTARTING", "restart_failed", "FAULT"),
    ("RESTARTING", "fatal_error", "FAULT"),
]


@pytest.mark.state_machine_tester(observation_state_machine_dag)
class TestObservationStateMachine(TransitionsStateMachineTester):
    """
    This class contains the test for the ska.low.mccs.state module.
    """
    @pytest.fixture
    def machine(self):
        """
        Fixture that returns the state machine under test in this class
        """
        yield ObservationStateMachine()
