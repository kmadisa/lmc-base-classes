"""
This module contains the tests for the ska.base.state_machine module.
"""
import json
import pytest

from ska.base.state_machine import BaseDeviceStateMachine, ObservationStateMachine
from .conftest import TransitionsStateMachineTester


with open("tests/schemas/base_device_state_machine.json", "r") as json_file:
    device_state_machine_spec = json.load(json_file)


@pytest.mark.state_machine_tester(device_state_machine_spec)
class BaseDeviceStateMachineTester(TransitionsStateMachineTester):
    """
    This class contains the test for the BaseDeviceStateMachine class.
    """
    @pytest.fixture
    def machine(self):
        """
        Fixture that returns the state machine under test in this class
        """
        yield BaseDeviceStateMachine()


with open("tests/schemas/observation_state_machine.json", "r") as json_file:
    observation_state_machine_spec = json.load(json_file)


@pytest.mark.state_machine_tester(observation_state_machine_spec)
class TestObservationStateMachine(TransitionsStateMachineTester):
    """
    This class contains the test for the ObservationStateMachine class.
    """
    @pytest.fixture
    def machine(self):
        """
        Fixture that returns the state machine under test in this class
        """
        yield ObservationStateMachine()
