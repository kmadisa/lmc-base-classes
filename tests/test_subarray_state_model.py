#########################################################################################
# -*- coding: utf-8 -*-
#
# This file is part of the SKASubarray project
#
#
#
#########################################################################################
"""Contain the tests for the SKASubarray."""

import itertools
# import re
import pytest

from tango import DevState
# from tango import DevState, DevSource, DevFailed

from ska.base.control_model import AdminMode, ObsState
# from ska.base.control_model import (
#     AdminMode, ControlMode, HealthState, ObsMode, ObsState, SimulationMode, TestMode
# )

from ska.base import SKASubarrayStateModel

@pytest.fixture(scope="function")
def model():
    """
    Yields an SKASubarrayStateModel.
    """
    yield SKASubarrayStateModel()

class TestSKASubarrayStateModel():
    """
    Test cases for SKASubarrayStateModel.
    """

    @pytest.mark.parametrize(
        'state_under_test, action_under_test',
        itertools.product(
            ["INIT_ENABLED", "DISABLED", "OFF", "FAULT", "EMPTY", "RESOURCING",
             "IDLE", "CONFIGURING", "READY", "SCANNING", "ABORTED", "OBSFAULT"],
            ["init_started", "init_succeeded", "init_failed", "to_notfitted",
             "to_offline", "to_online", "to_maintenance", "on_succeeded",
             "on_failed", "off_succeeded", "off_failed", "assign_started",
             "assign_succeeded_no_resources", "assign_succeeded_some_resources",
             "assign_failed", "configure_started", "configure_succeeded",
             "configure_failed", "scan_started", "scan_succeeded",
             "scan_failed", "end_scan_succeeded", "end_scan_failed",
             "abort_succeeded", "abort_failed", "reset_started",
             "reset_succeeded", "reset_failed", "restart_started",
             "restart_succeeded", "restart_failed"
             # to_fault? obsfault?
             ]
        )
    )
    def test_state_machine(self, model,
                           state_under_test, action_under_test):
        """
        Test the subarray state machine: for a given initial state and
        an action, does execution of that action, from that initial
        state, yield the expected results? If the action was not allowed
        from that initial state, does the device raise a DevFailed
        exception? If the action was allowed, does it result in the
        correct state transition?

        :todo: support starting in different memorised adminModes
        """

        states = {
            "UNKNOWN":
                (None, DevState.UNKNOWN, None),
            "FAULT":
                (None, DevState.FAULT, None),
            "INIT_ENABLED":
                ([AdminMode.ONLINE, AdminMode.MAINTENANCE], DevState.INIT, ObsState.EMPTY),
            "INIT_DISABLED":
                ([AdminMode.NOT_FITTED, AdminMode.OFFLINE], DevState.INIT, ObsState.EMPTY),
            "DISABLED":
                ([AdminMode.NOT_FITTED, AdminMode.OFFLINE], DevState.DISABLE, ObsState.EMPTY),
            "OFF":
                ([AdminMode.ONLINE, AdminMode.MAINTENANCE], DevState.OFF, ObsState.EMPTY),
            "EMPTY":
                ([AdminMode.ONLINE, AdminMode.MAINTENANCE], DevState.ON, ObsState.EMPTY),
            "RESOURCING":
                ([AdminMode.ONLINE, AdminMode.MAINTENANCE], DevState.ON, ObsState.RESOURCING),
            "IDLE":
                ([AdminMode.ONLINE, AdminMode.MAINTENANCE], DevState.ON, ObsState.IDLE),
            "CONFIGURING":
                ([AdminMode.ONLINE, AdminMode.MAINTENANCE], DevState.ON, ObsState.CONFIGURING),
            "READY":
                ([AdminMode.ONLINE, AdminMode.MAINTENANCE], DevState.ON, ObsState.READY),
            "SCANNING":
                ([AdminMode.ONLINE, AdminMode.MAINTENANCE], DevState.ON, ObsState.SCANNING),
            "ABORTED":
                ([AdminMode.ONLINE, AdminMode.MAINTENANCE], DevState.ON, ObsState.ABORTED),
            "RESETTING":
                ([AdminMode.ONLINE, AdminMode.MAINTENANCE], DevState.ON, ObsState.RESETTING),
            "RESTARTING":
                ([AdminMode.ONLINE, AdminMode.MAINTENANCE], DevState.ON, ObsState.RESTARTING),
            "OBSFAULT":
                ([AdminMode.ONLINE, AdminMode.MAINTENANCE], DevState.ON, ObsState.FAULT),
        }

        def assert_state(state):
            (admin_modes, state, obs_state) = states[state]
            if admin_modes is not None:
                assert model._admin_mode in admin_modes
            if state is not None:
                assert model._state == state
            if obs_state is not None:
                assert model._obs_state == obs_state

        def perform_action(action):
            getattr(model, action)()

        transitions = {
            ('UNKNOWN', 'init_started'): "INIT_ENABLED",
            ('INIT_ENABLED', 'init_succeeded'): 'OFF',
            ('INIT_ENABLED', 'init_failed'): 'FAULT',
            ('INIT_DISABLED', 'init_succeeded'): 'DISABLED',
            ('INIT_DISABLED', 'init_failed'): 'FAULT',
            ('DISABLED', 'to_notfitted'): "DISABLED",
            ('DISABLED', 'to_offline'): "DISABLED",
            ('DISABLED', 'to_online'): "OFF",
            ('DISABLED', 'to_maintenance'): "OFF",
            ('OFF', 'to_notfitted'): "DISABLED",
            ('OFF', 'to_offline'): "DISABLED",
            ('OFF', 'to_online'): "OFF",
            ('OFF', 'to_maintenance'): "OFF",
            ('OFF', 'on_succeeded'): "EMPTY",
            ('OFF', 'on_failed'): "FAULT",
            ('FAULT', 'reset_succeeded'): "OFF",
            ('FAULT', 'reset_failed'): "OFF",
            ('EMPTY', 'off_succeeded'): "OFF",
            ('EMPTY', 'off_failed'): "FAULT",
            ('EMPTY', 'assign_started'): "RESOURCING",
            ("EMPTY", 'to_fault'): "OBSFAULT",
            ('RESOURCING', 'assign_succeeded_some_resources'): "IDLE",
            ('RESOURCING', 'assign_succeeded_no_resources'): "EMPTY",
            ('RESOURCING', 'assign_failed'): "OBSFAULT",
            ('IDLE', 'assign_started'): "RESOURCING",
            ('IDLE', 'configure_started'): "CONFIGURING",
            ('IDLE', 'abort_succeeded'): "ABORTED",
            ('IDLE', 'abort_failed'): "OBSFAULT",
            ('CONFIGURING', 'configure_succeeded'): "READY",
            ('CONFIGURING', 'configure_failed'): "OBSFAULT",
            ('CONFIGURING', 'abort_succeeded'): "ABORTED",
            ('CONFIGURING', 'abort_failed'): "OBSFAULT",
            ('READY', 'end_succeeded'): "IDLE",
            ('READY', 'end_failed'): "OBSFAULT",
            ('READY', 'configure_started'): "CONFIGURING",
            ('READY', 'abort_succeeded'): "ABORTED",
            ('READY', 'abort_failed'): "OBSFAULT",
            ('READY', 'scan_started'): "SCANNING",
            ('SCANNING', 'scan_succeeded'): "READY",
            ('SCANNING', 'scan_failed'): "OBSFAULT",
            ('SCANNING', 'end_scan_succeeded'): "READY",
            ('SCANNING', 'end_scan_failed'): "OBSFAULT",
            ('SCANNING', 'abort_succeeded'): "ABORTED",
            ('SCANNING', 'abort_failed'): "OBSFAULT",
            ('ABORTED', 'reset_started'): "RESETTING",
            ('ABORTED', 'restart_started'): "RESTARTING",
            ('OBSFAULT', 'reset_started'): "RESETTING",
            ('OBSFAULT', 'restart_started'): "RESTARTING",
            ('RESETTING', 'reset_succeeded'): "IDLE",
            ('RESETTING', 'reset_failed'): "OBSFAULT",
            ('RESTARTING', 'restart_succeeded'): "EMPTY",
            ('RESTARTING', 'restart_failed'): "OBSFAULT",
        }

        setups = {
            "INIT_ENABLED": ['init_started'],
            "FAULT": ['init_started', 'init_failed'],
            "OFF": ['init_started', 'init_succeeded'],
            "DISABLED": ['init_started', 'init_succeeded', 'to_offline'],
            "EMPTY": ['init_started', 'init_succeeded', 'on_succeeded'],
            "RESOURCING": [
                'init_started', 'init_succeeded', 'on_succeeded',
                'assign_started'
            ],
            "IDLE": [
                'init_started', 'init_succeeded', 'on_succeeded',
                'assign_started', 'assign_succeeded_some_resources'],
            "CONFIGURING": [
                'init_started', 'init_succeeded', 'on_succeeded',
                'assign_started', 'assign_succeeded_some_resources',
                'configure_started'
            ],
            "READY": [
                'init_started', 'init_succeeded', 'on_succeeded',
                'assign_started', 'assign_succeeded_some_resources',
                'configure_started', 'configure_succeeded'
            ],
            "SCANNING": [
                'init_started', 'init_succeeded', 'on_succeeded',
                'assign_started', 'assign_succeeded_some_resources',
                'configure_started', 'configure_succeeded', 'scan_started'
            ],
            "ABORTED": [
                'init_started', 'init_succeeded', 'on_succeeded',
                'assign_started', 'assign_succeeded_some_resources',
                'abort_succeeded'
            ],
            "OBSFAULT": [
                'init_started', 'init_succeeded', 'on_succeeded', 'to_fault'
            ],
            "RESETTING": [
                'init_started', 'init_succeeded', 'on_succeeded',
                'assign_started', 'assign_succeeded_some_resources',
                'abort_succeeded', 'reset_started'
            ],
            "RESTARTING": [
                'init_started', 'init_succeeded', 'on_succeeded',
                'assign_started', 'assign_succeeded_some_resources',
                'abort_succeeded', 'restart_started'
            ],
        }

        assert_state("UNKNOWN")

        # Put the device into the state under test
        for action in setups[state_under_test]:
            perform_action(action)

        # Check that we are in the state under test
        assert_state(state_under_test)

        # Test that the action under test does what we expect it to
        if (state_under_test, action_under_test) in transitions:
            # Action should succeed
            perform_action(action_under_test)
            assert_state(transitions[(state_under_test, action_under_test)])
        else:
            # Action should fail and the state should not change
            with pytest.raises(ValueError):
                perform_action(action_under_test)
            assert_state(state_under_test)
