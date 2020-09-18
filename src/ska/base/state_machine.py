"""
This module contains specifications of SKA state machines.
"""
from transitions import Machine, State
from tango import DevState

from ska.base.control_model import AdminMode, ObsState


class DeviceStateMachine(Machine):
    """
    State machine for an SKA base device.
    Supports INIT, FAULT, DISABLED, STANDBY, OFF and ON states.
    """

    def __init__(self, op_state_callback=None):
        """
        Initialises the state model.

        :param op_state_callback: A callback to be called when a
            transition implies a change to op state
        :type op_state_callback: callable
        """
        self._op_state = None
        self._op_state_callback = op_state_callback

        states = [
            State("UNINITIALISED"),
            State("INIT", on_enter="_init_entered"),
            State("FAULT", on_enter="_fault_entered"),
            State("DISABLED", on_enter="_disabled_entered"),
            State("STANDBY", on_enter="_standby_entered"),
            State("OFF", on_enter="_off_entered"),
            State("ON", on_enter="_on_entered"),
        ]

        transitions = [
            {
                "source": "UNINITIALISED",
                "trigger": "init_started",
                "dest": "INIT",
            },
            {
                "source": ["INIT", "FAULT", "DISABLED", "STANDBY", "OFF", "ON"],
                "trigger": "fatal_error",
                "dest": "FAULT",
            },
            {
                "source": "INIT",
                "trigger": "init_succeeded_disabled",
                "dest": "DISABLED",
            },
            {
                "source": "INIT",
                "trigger": "init_succeeded_standby",
                "dest": "STANDBY",
            },
            {
                "source": "INIT",
                "trigger": "init_succeeded_off",
                "dest": "OFF",
            },
            {
                "source": "INIT",
                "trigger": "init_failed",
                "dest": "FAULT",
            },
            {
                "source": "FAULT",
                "trigger": "reset_succeeded_disabled",
                "dest": "DISABLED",
            },
            {
                "source": "FAULT",
                "trigger": "reset_succeeded_standby",
                "dest": "STANDBY",
            },
            {
                "source": "FAULT",
                "trigger": "reset_succeeded_off",
                "dest": "OFF",
            },
            {
                "source": "FAULT",
                "trigger": "reset_failed",
                "dest": "FAULT",
            },
            {
                "source": ["DISABLED", "OFF"],
                "trigger": "standby_succeeded",
                "dest": "STANDBY",
            },
            {
                "source": ["DISABLED", "OFF"],
                "trigger": "standby_failed",
                "dest": "FAULT",
            },
            {
                "source": ["STANDBY", "OFF"],
                "trigger": "disable_succeeded",
                "dest": "DISABLED",
            },
            {
                "source": ["STANDBY", "OFF"],
                "trigger": "disable_failed",
                "dest": "FAULT",
            },
            {
                "source": ["DISABLED", "STANDBY", "ON"],
                "trigger": "off_succeeded",
                "dest": "OFF",
            },
            {
                "source": ["DISABLED", "STANDBY", "ON"],
                "trigger": "off_failed",
                "dest": "FAULT",
            },
            {
                "source": "OFF",
                "trigger": "on_succeeded",
                "dest": "ON",
            },
            {
                "source": "OFF",
                "trigger": "on_failed",
                "dest": "FAULT",
            },
        ]

        super().__init__(
            states=states,
            initial="UNINITIALISED",
            transitions=transitions,
        )

    def _init_entered(self):
        """
        called when the state machine enters the INIT state.
        """
        self._update_op_state(DevState.INIT)

    def _fault_entered(self):
        """
        called when the state machine enters the FAULT state.
        """
        self._update_op_state(DevState.FAULT)

    def _disabled_entered(self):
        """
        called when the state machine enters the DISABLED state.
        """
        self._update_op_state(DevState.DISABLE)

    def _standby_entered(self):
        """
        called when the state machine enters the STANDBY state.
        """
        self._update_op_state(DevState.STANDBY)

    def _off_entered(self):
        """
        called when the state machine enters the OFF state.
        """
        self._update_op_state(DevState.OFF)

    def _on_entered(self):
        """
        called when the state machine enters the ON state.
        """
        self._update_op_state(DevState.ON)

    def _update_op_state(self, op_state):
        """
        Helper method: sets this state models op_state, and calls the
        op_state callback if one exists

        :param op_state: the new op state value
        :type op_state: DevState
        """
        if self._op_state != op_state:
            self._op_state = op_state
            if self._op_state_callback is not None:
                self._op_state_callback(self._op_state)


class ObservationStateMachine(Machine):
    """
    The observation state machine used by an observing subarray, per
    ADR-8.
    """

    def __init__(self, obs_state_callback=None):
        """
        Initialises the model.

        :param obs_state_callback: A callback to be called when a
            transition causes a change to device obs_state
        :type obs_state_callback: callable
        """
        self._obs_state = ObsState.EMPTY
        self._obs_state_callback = obs_state_callback

        states = [obs_state.name for obs_state in ObsState]
        transitions = [
            {
                "source": "*",
                "trigger": "fatal_error",
                "dest": ObsState.FAULT.name,
            },
            {
                "source": [ObsState.EMPTY.name, ObsState.IDLE.name],
                "trigger": "assign_started",
                "dest": ObsState.RESOURCING.name,
            },
            {
                "source": ObsState.IDLE.name,
                "trigger": "release_started",
                "dest": ObsState.RESOURCING.name,
            },
            {
                "source": ObsState.RESOURCING.name,
                "trigger": "resourcing_succeeded_some_resources",
                "dest": ObsState.IDLE.name,
            },
            {
                "source": ObsState.RESOURCING.name,
                "trigger": "resourcing_succeeded_no_resources",
                "dest": ObsState.EMPTY.name,
            },
            {
                "source": ObsState.RESOURCING.name,
                "trigger": "resourcing_failed",
                "dest": ObsState.FAULT.name,
            },
            {
                "source": [ObsState.IDLE.name, ObsState.READY.name],
                "trigger": "configure_started",
                "dest": ObsState.CONFIGURING.name,
            },
            {
                "source": ObsState.CONFIGURING.name,
                "trigger": "configure_succeeded",
                "dest": ObsState.READY.name,
            },
            {
                "source": ObsState.CONFIGURING.name,
                "trigger": "configure_failed",
                "dest": ObsState.FAULT.name,
            },
            {
                "source": ObsState.READY.name,
                "trigger": "end_succeeded",
                "dest": ObsState.IDLE.name,
            },
            {
                "source": ObsState.READY.name,
                "trigger": "end_failed",
                "dest": ObsState.FAULT.name,
            },
            {
                "source": ObsState.READY.name,
                "trigger": "scan_started",
                "dest": ObsState.SCANNING.name,
            },
            {
                "source": ObsState.SCANNING.name,
                "trigger": "scan_succeeded",
                "dest": ObsState.READY.name,
            },
            {
                "source": ObsState.SCANNING.name,
                "trigger": "scan_failed",
                "dest": ObsState.FAULT.name,
            },
            {
                "source": ObsState.SCANNING.name,
                "trigger": "end_scan_succeeded",
                "dest": ObsState.READY.name,
            },
            {
                "source": ObsState.SCANNING.name,
                "trigger": "end_scan_failed",
                "dest": ObsState.FAULT.name,
            },
            {
                "source": [
                    ObsState.IDLE.name,
                    ObsState.CONFIGURING.name,
                    ObsState.READY.name,
                    ObsState.SCANNING.name,
                    ObsState.RESETTING.name,
                ],
                "trigger": "abort_started",
                "dest": ObsState.ABORTING.name,
            },
            {
                "source": ObsState.ABORTING.name,
                "trigger": "abort_succeeded",
                "dest": ObsState.ABORTED.name,
            },
            {
                "source": ObsState.ABORTING.name,
                "trigger": "abort_failed",
                "dest": ObsState.FAULT.name,
            },
            {
                "source": [ObsState.ABORTED.name, ObsState.FAULT.name],
                "trigger": "obs_reset_started",
                "dest": ObsState.RESETTING.name,
            },
            {
                "source": ObsState.RESETTING.name,
                "trigger": "obs_reset_succeeded",
                "dest": ObsState.IDLE.name,
            },
            {
                "source": ObsState.RESETTING.name,
                "trigger": "obs_reset_failed",
                "dest": ObsState.FAULT.name,
            },
            {
                "source": [ObsState.ABORTED.name, ObsState.FAULT.name],
                "trigger": "restart_started",
                "dest": ObsState.RESTARTING.name,
            },
            {
                "source": ObsState.RESTARTING.name,
                "trigger": "restart_succeeded",
                "dest": ObsState.EMPTY.name,
            },
            {
                "source": ObsState.RESTARTING.name,
                "trigger": "restart_failed",
                "dest": ObsState.FAULT.name,
            },
        ]

        super().__init__(
            states=states,
            initial=ObsState.EMPTY.name,
            transitions=transitions,
            after_state_change=self._obs_state_changed,
        )

    def _obs_state_changed(self):
        """
        State machine callback that is called every time the obs_state
        changes. Responsible for ensuring that callbacks are called.
        """
        obs_state = ObsState[self.state]
        if self._obs_state != obs_state:
            self._obs_state = obs_state
            if self._obs_state_callback is not None:
                self._obs_state_callback(self._obs_state)
