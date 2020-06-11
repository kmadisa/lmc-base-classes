# -*- coding: utf-8 -*-
#
# This file is part of the SKAObsDevice project
#
#
#
""" SKAObsDevice

A generic base device for Observations for SKA. It inherits SKABaseDevice
class. Any device implementing an obsMode will inherit from SKAObsDevice
instead of just SKABaseDevice.
"""

# Additional import
# PROTECTED REGION ID(SKAObsDevice.additionnal_import) ENABLED START #
# Tango imports
from tango import DevState
from tango.server import run, attribute

# SKA specific imports
from ska.base import SKABaseDevice, SKABaseDeviceStateModel
from ska.base.control_model import AdminMode, ObsMode, ObsState, guard
# PROTECTED REGION END #    //  SKAObsDevice.additionnal_imports

__all__ = ["SKAObsDevice", "SKAObsDeviceStateModel", "main"]


class SKAObsDeviceStateModel(SKABaseDeviceStateModel):
    """
    Implements the state model for the SKABaseDevice
    """
    guard.register(
        "obs_state",
        lambda model, obs_state: model._obs_state == obs_state
    )
    guard.register(
        "obs_states",
        lambda model, obs_states: model._obs_state in obs_states
    )
    guard.register(
        "is_obs",  # shortcut for very common use case
        lambda model, obs_states:
            model._state == DevState.ON and
            model._admin_mode in [AdminMode.ONLINE, AdminMode.MAINTENANCE] and
            model._obs_state in obs_states
    )

    def __init__(self, state_callback=None):
        """
        Initialises the model. Note that this does not imply moving to
        INIT state. The INIT state is managed by the model itself.
        """
        super().__init__(state_callback)
        self._obs_state = None

    def init_started(self):
        """
        Call this method to let the model know that the device's
        `init_device` method has been called.
        """
        super().init_started()
        self._obs_state = ObsState.EMPTY

class SKAObsDevice(SKABaseDevice):
    """
    A generic base device for Observations for SKA.
    """
    state_model_class = SKAObsDeviceStateModel

    # PROTECTED REGION ID(SKAObsDevice.class_variable) ENABLED START #

    # PROTECTED REGION END #    //  SKAObsDevice.class_variable

    # -----------------
    # Device Properties
    # -----------------

    # ----------
    # Attributes
    # ----------

    obsState = attribute(
        dtype=ObsState,
        polling_period=1000,
        doc="Observing State",
    )

    obsMode = attribute(
        dtype=ObsMode,
        polling_period=1000,
        doc="Observing Mode",
    )

    configurationProgress = attribute(
        dtype='uint16',
        unit="%",
        max_value=100,
        min_value=0,
        doc="Percentage configuration progress",
    )

    configurationDelayExpected = attribute(
        dtype='uint16',
        unit="seconds",
        doc="Configuration delay expected in seconds",
    )

    # ---------------
    # General methods
    # ---------------
    def do_init_device(self):
        """
        Method that initialises device attribute and other internal
        values. This method is called, possibly asynchronously, by
        ``init_device``. Subclasses that have no need to override the
        default implementation of state management and asynchrony may
        leave ``init_device`` alone and override this method instead.
        """
        (return_code, message) = super().do_init_device()
        self._obs_mode = ObsMode.IDLE

        self._config_progress = 0
        self._config_delay_expected = 0

        return (return_code, message)

    def always_executed_hook(self):
        # PROTECTED REGION ID(SKAObsDevice.always_executed_hook) ENABLED START #
        pass
        # PROTECTED REGION END #    //  SKAObsDevice.always_executed_hook

    def delete_device(self):
        # PROTECTED REGION ID(SKAObsDevice.delete_device) ENABLED START #
        pass
        # PROTECTED REGION END #    //  SKAObsDevice.delete_device

    # ------------------
    # Attributes methods
    # ------------------

    def read_obsState(self):
        # PROTECTED REGION ID(SKAObsDevice.obsState_read) ENABLED START #
        """Reads Observation State of the device"""
        return self.state_model._obs_state
        # PROTECTED REGION END #    //  SKAObsDevice.obsState_read

    def read_obsMode(self):
        # PROTECTED REGION ID(SKAObsDevice.obsMode_read) ENABLED START #
        """Reads Observation Mode of the device"""
        return self._obs_mode
        # PROTECTED REGION END #    //  SKAObsDevice.obsMode_read

    def read_configurationProgress(self):
        # PROTECTED REGION ID(SKAObsDevice.configurationProgress_read) ENABLED START #
        """Reads percentage configuration progress of the device"""
        return self._config_progress
        # PROTECTED REGION END #    //  SKAObsDevice.configurationProgress_read

    def read_configurationDelayExpected(self):
        # PROTECTED REGION ID(SKAObsDevice.configurationDelayExpected_read) ENABLED START #
        """Reads expected Configuration Delay in seconds"""
        return self._config_delay_expected
        # PROTECTED REGION END #    //  SKAObsDevice.configurationDelayExpected_read

    # --------
    # Commands
    # --------

# ----------
# Run server
# ----------


def main(args=None, **kwargs):
    # PROTECTED REGION ID(SKAObsDevice.main) ENABLED START #
    return run((SKAObsDevice,), args=args, **kwargs)
    # PROTECTED REGION END #    //  SKAObsDevice.main


if __name__ == '__main__':
    main()
