# -*- coding: utf-8 -*-
#
# This file is part of the SKASubarray project
#
#
#
""" SKASubarray

A SubArray handling device. It allows the assigning/releasing of resources
into/from Subarray, configuring capabilities, and exposes the related
information like assigned resources, configured capabilities, etc.
"""
# PROTECTED REGION ID(SKASubarray.additionnal_import) ENABLED START #
from tango import DebugIt
from tango import DevState
from tango.server import run, attribute, command
from tango.server import device_property

# SKA specific imports
from ska.base import SKAObsDevice, SKAObsDeviceStateModel
from ska.base.control_model import ObsState, ReturnCode
from ska.base.control_model import ActionCommand, DualActionCommand
from ska.base.faults import CapabilityValidationError
# PROTECTED REGION END #    //  SKASubarray.additionnal_imports

__all__ = ["SKASubarray", "SKASubarrayStateModel", "main"]


class SKASubarrayStateModel(SKAObsDeviceStateModel):
    """
    Implements the state model for the SKASubarray
    """
    _subarray_transitions = {
        ('OFF', 'on_succeeded'): (
            "EMPTY",
            lambda self: self._set_state(DevState.ON)
        ),
        ('OFF', 'on_failed'): (
            "FAULT",
            lambda self: self._set_state(DevState.FAULT)
        ),
        ('EMPTY', 'off_succeeded'): (
            "OFF",
            lambda self: self._set_state(DevState.OFF)
        ),
        ('EMPTY', 'off_failed'): (
            "FAULT",
            lambda self: self._set_state(DevState.FAULT)
        ),
        ('EMPTY', 'assign_started'): (
            "RESOURCING",
            lambda self: self._set_obs_state(ObsState.RESOURCING)
        ),
        ('EMPTY', 'fatal_error'): (
            "OBSFAULT",
            lambda self: self._set_obs_state(ObsState.FAULT)
        ),
        ('RESOURCING', 'resourcing_succeeded_some_resources'): (
            "IDLE",
            lambda self: self._set_obs_state(ObsState.IDLE)
        ),
        ('RESOURCING', 'resourcing_succeeded_no_resources'): (
            "EMPTY",
            lambda self: self._set_obs_state(ObsState.EMPTY)
        ),
        ('RESOURCING', 'resourcing_failed'): (
            "OBSFAULT",
            lambda self: self._set_obs_state(ObsState.FAULT)
        ),
        ('RESOURCING', 'fatal_error'): (
            "OBSFAULT",
            lambda self: self._set_obs_state(ObsState.FAULT)
        ),
        ('IDLE', 'assign_started'): (
            "RESOURCING",
            lambda self: self._set_obs_state(ObsState.RESOURCING)
        ),
        ('IDLE', 'release_started'): (
            "RESOURCING",
            lambda self: self._set_obs_state(ObsState.RESOURCING)
        ),
        ('IDLE', 'configure_started'): (
            "CONFIGURING",
            lambda self: self._set_obs_state(ObsState.CONFIGURING)
        ),
        ('IDLE', 'abort_started'): (
            "ABORTING",
            lambda self: self._set_obs_state(ObsState.ABORTING)
        ),
        ('IDLE', 'fatal_error'): (
            "OBSFAULT",
            lambda self: self._set_obs_state(ObsState.FAULT)
        ),
        ('CONFIGURING', 'configure_succeeded'): (
            "READY",
            lambda self: self._set_obs_state(ObsState.READY)
        ),
        ('CONFIGURING', 'configure_failed'): (
            "OBSFAULT",
            lambda self: self._set_obs_state(ObsState.FAULT)
        ),
        ('CONFIGURING', 'abort_started'): (
            "ABORTING",
            lambda self: self._set_obs_state(ObsState.ABORTING)
        ),
        ('CONFIGURING', 'fatal_error'): (
            "OBSFAULT",
            lambda self: self._set_obs_state(ObsState.FAULT)
        ),
        ('READY', 'end_succeeded'): (
            "IDLE",
            lambda self: self._set_obs_state(ObsState.IDLE)
        ),
        ('READY', 'end_failed'): (
            "OBSFAULT",
            lambda self: self._set_obs_state(ObsState.FAULT)
        ),
        ('READY', 'configure_started'): (
            "CONFIGURING",
            lambda self: self._set_obs_state(ObsState.CONFIGURING)
        ),
        ('READY', 'abort_started'): (
            "ABORTING",
            lambda self: self._set_obs_state(ObsState.ABORTING)
        ),
        ('READY', 'scan_started'): (
            "SCANNING",
            lambda self: self._set_obs_state(ObsState.SCANNING)
        ),
        ('READY', 'fatal_error'): (
            "OBSFAULT",
            lambda self: self._set_obs_state(ObsState.FAULT)
        ),
        ('SCANNING', 'scan_succeeded'): (
            "READY",
            lambda self: self._set_obs_state(ObsState.READY)
        ),
        ('SCANNING', 'scan_failed'): (
            "OBSFAULT",
            lambda self: self._set_obs_state(ObsState.FAULT)
        ),
        ('SCANNING', 'end_scan_succeeded'): (
            "READY",
            lambda self: self._set_obs_state(ObsState.READY)
        ),
        ('SCANNING', 'end_scan_failed'): (
            "OBSFAULT",
            lambda self: self._set_obs_state(ObsState.FAULT)
        ),
        ('SCANNING', 'abort_started'): (
            "ABORTING",
            lambda self: self._set_obs_state(ObsState.ABORTING)
        ),
        ('SCANNING', 'fatal_error'): (
            "OBSFAULT",
            lambda self: self._set_obs_state(ObsState.FAULT)
        ),
        ('ABORTING', 'abort_succeeded'): (
            "ABORTED",
            lambda self: self._set_obs_state(ObsState.ABORTED)
        ),
        ('ABORTING', 'abort_failed'): (
            "OBSFAULT",
            lambda self: self._set_obs_state(ObsState.FAULT)
        ),
        ('ABORTING', 'fatal_error'): (
            "OBSFAULT",
            lambda self: self._set_obs_state(ObsState.FAULT)
        ),
        ('ABORTED', 'obs_reset_started'): (
            "RESETTING",
            lambda self: self._set_obs_state(ObsState.RESETTING)
        ),
        ('ABORTED', 'restart_started'): (
            "RESTARTING",
            lambda self: self._set_obs_state(ObsState.RESTARTING)
        ),
        ('ABORTED', 'fatal_error'): (
            "OBSFAULT",
            lambda self: self._set_obs_state(ObsState.FAULT)
        ),
        ('OBSFAULT', 'obs_reset_started'): (
            "RESETTING",
            lambda self: self._set_obs_state(ObsState.RESETTING)
        ),
        ('OBSFAULT', 'restart_started'): (
            "RESTARTING",
            lambda self: self._set_obs_state(ObsState.RESTARTING)
        ),
        ('OBSFAULT', 'fatal_error'): (
            "OBSFAULT",
            lambda self: self._set_obs_state(ObsState.FAULT)
        ),
        ('RESETTING', 'obs_reset_succeeded'): (
            "IDLE",
            lambda self: self._set_obs_state(ObsState.IDLE)
        ),
        ('RESETTING', 'obs_reset_failed'): (
            "OBSFAULT",
            lambda self: self._set_obs_state(ObsState.FAULT)
        ),
        ('RESETTING', 'fatal_error'): (
            "OBSFAULT",
            lambda self: self._set_obs_state(ObsState.FAULT)
        ),
        ('RESTARTING', 'restart_succeeded'): (
            "EMPTY",
            lambda self: self._set_obs_state(ObsState.EMPTY)
        ),
        ('RESTARTING', 'restart_failed'): (
            "OBSFAULT",
            lambda self: self._set_obs_state(ObsState.FAULT)
        ),
        ('RESTARTING', 'fatal_error'): (
            "OBSFAULT",
            lambda self: self._set_obs_state(ObsState.FAULT)
        ),
    }

    def __init__(self, admin_mode_callback=None, state_callback=None, obs_state_callback=None):
        """
        Initialises the model. Note that this does not imply moving to
        INIT state. The INIT state is managed by the model itself.
        """
        super().__init__(
            admin_mode_callback=admin_mode_callback,
            state_callback=state_callback,
            obs_state_callback=obs_state_callback
        )
        self.update_transitions(self._subarray_transitions)


class SKASubarray(SKAObsDevice):
    """
    Implements the SKA SubArray device
    """
    class InitCommand(SKAObsDevice.InitCommand):
        """
        A class for the SKASubarray's init_device() "command".
        """
        def do(self, target, logger):
            """
            Stateless hook for device initialisation.

            :param target: the object that this command acts upon; for
                example, the SKASubarray device for which this class
                implements the command
            :type target: object
            :param logger: the logger for this command.
            :type logger: a logger that implements the standard library
                logger interface
            :return: A tuple containing a return code and a string
                message indicating status. The message is for
                information purpose only.
            :rtype: (ReturnCode, str)
            """
            (return_code, message) = super().do(target, logger)

            # Initialize attribute values.
            target._activation_time = 0.0
            target._assigned_resources = [""]
            target._assigned_resources.clear()

            # device._configured_capabilities is will be kept as a
            # dictionary internally. The keys and value will represent
            # the capability type name and the number of instances,
            # respectively.
            try:
                target._configured_capabilities = dict.fromkeys(
                    target.CapabilityTypes,
                    0
                )
            except TypeError:
                # Might need to have the device property be mandatory in the database.
                target._configured_capabilities = {}

            message = "SKASubarray initialisation completed OK"
            logger.info(message)
            return (ReturnCode.OK, message)

    class OnCommand(ActionCommand):
        """
        A class for the SKASubarray's On() command.
        """
        def __init__(self, target, state_model, logger=None):
            """
            Constructor for OnCommand

            :param target: the object that this command acts upon; for
                example, the SKASubarray device for which this class
                implements the command
            :type target: object
            :param state_model: the state model that this command uses
                 to check that it is allowed to run, and that it drives
                 with actions.
            :type state_model: SKABaseClassStateModel or a subclass of
                same
            :param logger: the logger to be used by this Command. If not
                provided, then a default module logger will be used.
            :type logger: a logger that implements the standard library
                logger interface
            """
            super().__init__(target, state_model, "on", logger=logger)

        def do(self, target, logger):
            """
            Stateless hook for On() command functionality.

            :param target: the object that this command acts upon; for
                example, the SKASubarray device for which this class
                implements the command
            :type target: object
            :param logger: the logger for this Command.
            :type logger: a logger that implements the standard library
                logger interface
            :return: A tuple containing a return code and a string
                message indicating status. The message is for
                information purpose only.
            :rtype: (ReturnCode, str)
            """
            message = "On command completed OK"
            logger.info(message)
            return (ReturnCode.OK, message)

    class OffCommand(ActionCommand):
        """
        A class for the SKASubarray's Off() command.
        """
        def __init__(self, target, state_model, logger=None):
            """
            Constructor for OffCommand

            :param target: the object that this command acts upon; for
                example, the SKASubarray device for which this class
                implements the command
            :type target: object
            :param state_model: the state model that this command uses
                 to check that it is allowed to run, and that it drives
                 with actions.
            :type state_model: SKABaseClassStateModel or a subclass of
                same
            :param logger: the logger to be used by this Command. If not
                provided, then a default module logger will be used.
            :type logger: a logger that implements the standard library
                logger interface
            """
            super().__init__(target, state_model, "off", logger)

        def do(self, target, logger):
            """
            Stateless hook for Off() command functionality.

            :param target: the object that this command acts upon; for
                example, the SKASubarray device for which this class
                implements the command
            :type target: object
            :param logger: the logger for this Command.
            :type logger: a logger that implements the standard library
                logger interface
            :return: A tuple containing a return code and a string
                message indicating status. The message is for
                information purpose only.
            :rtype: (ReturnCode, str)
            """
            message = "Off command completed OK"
            logger.info(message)
            return (ReturnCode.OK, message)

    class _ResourcingCommand(DualActionCommand):
        """
        An abstract base class for SKASubarray's resourcing commands.
        """
        def succeeded(self):
            """
            Action to take on successful completion of a resourcing
            command.
            """
            if self.target.is_resourced():
                action = "resourcing_succeeded_some_resources"
            else:
                action = "resourcing_succeeded_no_resources"
            self.state_model.perform_action(action)

        def failed(self):
            """
            Action to take on failed completion of a resourcing command.
            """
            self._state_model.perform_action("resourcing_failed")

    class AssignResourcesCommand(_ResourcingCommand):
        """
        A class for SKASubarray's AssignResources() command.
        """
        def __init__(self, target, state_model, logger=None):
            """
            Constructor for AssignResourcesCommand

            :param target: the object that this command acts upon; for
                example, the SKASubarray device for which this class
                implements the command
            :type target: object
            :param state_model: the state model that this command uses
                 to check that it is allowed to run, and that it drives
                 with actions.
            :type state_model: SKABaseClassStateModel or a subclass of
                same
            :param logger: the logger to be used by this Command. If not
                provided, then a default module logger will be used.
            :type logger: a logger that implements the standard library
                logger interface
            """
            super().__init__(target, state_model, "assign", logger)

        def do(self, target, logger, argin):
            """
            Stateless hook for AssignResources() command functionality.

            :param target: the object that this command acts upon; for
                example, the SKASubarray device for which this class
                implements the command
            :type target: object
            :param logger: the logger for this Command.
            :type logger: a logger that implements the standard library
                logger interface
            :param argin: The resources to be assigned
            :type argin: list of str
            :return: A tuple containing a return code and a string
                message indicating status. The message is for
                information purpose only.
            :rtype: (ReturnCode, str)
            """
            target._assign_resources(argin)

            message = "AssignResources command completed OK"
            logger.info(message)
            return (ReturnCode.OK, message)

    class ReleaseResourcesCommand(_ResourcingCommand):
        """
        A class for SKASubarray's ReleaseResources() command.
        """
        def __init__(self, target, state_model, logger=None):
            """
            Constructor for OnCommand()

            :param target: the object that this command acts upon; for
                example, the SKASubarray device for which this class
                implements the command
            :type target: object
            :param state_model: the state model that this command uses
                 to check that it is allowed to run, and that it drives
                 with actions.
            :type state_model: SKABaseClassStateModel or a subclass of
                same
            :param logger: the logger to be used by this Command. If not
                provided, then a default module logger will be used.
            :type logger: a logger that implements the standard library
                logger interface
            """
            super().__init__(target, state_model, "release", logger)

        def do(self, target, logger, argin):
            """
            Stateless hook for ReleaseResources() command functionality.

            :param target: the object that this command acts upon; for
                example, the SKASubarray device for which this class
                implements the command
            :type target: object
            :param logger: the logger for this Command.
            :type logger: a logger that implements the standard library
                logger interface
            :param argin: The resources to be assigned
            :type argin: list of str
            :return: A tuple containing a return code and a string
                message indicating status. The message is for
                information purpose only.
            :rtype: (ReturnCode, str)
            """
            target._release_resources(argin)

            message = "ReleaseResources command completed OK"
            logger.info(message)
            return (ReturnCode.OK, message)

    class ReleaseAllResourcesCommand(ReleaseResourcesCommand):
        """
        A class for SKASubarray's ReleaseAllResources() command.
        """
        def do(self, target, logger):
            """
            Stateless hook for ReleaseAllResources() command functionality.

            :param target: the object that this command acts upon; for
                example, the SKASubarray device for which this class
                implements the command
            :type target: object
            :param logger: the logger for this Command.
            :type logger: a logger that implements the standard library
                logger interface
            :param argin: The resources to be assigned
            :type argin: list of str
            :return: A tuple containing a return code and a string
                message indicating status. The message is for
                information purpose only.
            :rtype: (ReturnCode, str)
            """
            target._release_all_resources()

            message = "ReleaseAllResources command completed OK"
            logger.info(message)
            return (ReturnCode.OK, message)

    class ConfigureCommand(DualActionCommand):
        """
        A class for SKASubarray's Configure() command.
        """
        def __init__(self, target, state_model, logger=None):
            """
            Constructor for ConfigureCommand

            :param target: the object that this command acts upon; for
                example, the SKASubarray device for which this class
                implements the command
            :type target: object
            :param state_model: the state model that this command uses
                 to check that it is allowed to run, and that it drives
                 with actions.
            :type state_model: SKABaseClassStateModel or a subclass of
                same
            :param logger: the logger to be used by this Command. If not
                provided, then a default module logger will be used.
            :type logger: a logger that implements the standard library
                logger interface
            """
            super().__init__(target, state_model, "configure", logger)

        @staticmethod
        def _validate_input_sizes(argin):
            """
            Check the validity of the input parameters passed to the
            Configure command.

            :param argin: A tuple of two lists representing [number of
                instances][capability types]
            :type argin: tango.DevVarLongStringArray
            :raises ValueError: If the two lists are not equal in length.
            """
            capabilities_instances, capability_types = argin
            if len(capabilities_instances) != len(capability_types):
                raise ValueError("Argin value lists size mismatch.")

        def do(self, target, logger, argin):
            """
            Stateless hook for Configure() command functionality.

            :param target: the object that this command acts upon; for
                example, the SKASubarray device for which this class
                implements the command
            :type target: object
            :param logger: the logger for this Command.
            :type logger: a logger that implements the standard library
                logger interface
            :param argin: The configuration
            :type argin: list of str
            :return: A tuple containing a return code and a string
                message indicating status. The message is for
                information purpose only.
            :rtype: (ReturnCode, str)
            """
            capabilities_instances, capability_types = argin
            target._validate_capability_types(capability_types)
            self._validate_input_sizes(argin)

            # Perform the configuration.
            for capability_instances, capability_type in zip(
                    capabilities_instances, capability_types):
                target._configured_capabilities[capability_type] += capability_instances

            message = "Configure command completed OK"
            logger.info(message)
            return (ReturnCode.OK, message)

    class ScanCommand(DualActionCommand):
        """
        A class for SKASubarray's Scan() command.
        """
        def __init__(self, target, state_model, logger=None):
            """
            Constructor for ScanCommand

            :param target: the object that this command acts upon; for
                example, the SKASubarray device for which this class
                implements the command
            :type target: object
            :param state_model: the state model that this command uses
                 to check that it is allowed to run, and that it drives
                 with actions.
            :type state_model: SKABaseClassStateModel or a subclass of
                same
            :param logger: the logger to be used by this Command. If not
                provided, then a default module logger will be used.
            :type logger: a logger that implements the standard library
                logger interface
            """
            super().__init__(target, state_model, "scan", logger)

        def do(self, target, logger, argin):
            """
            Stateless hook for Scan() command functionality.

            :param target: the object that this command acts upon; for
                example, the SKASubarray device for which this class
                implements the command
            :type target: object
            :param logger: the logger for this Command.
            :type logger: a logger that implements the standard library
                logger interface
            :param argin: Scan info
            :type argin: str
            :return: A tuple containing a return code and a string
                message indicating status. The message is for
                information purpose only.
            :rtype: (ReturnCode, str)
            """
            message = "Scan command STARTED"
            logger.info(message)
            return (ReturnCode.STARTED, message)

    class EndScanCommand(ActionCommand):
        """
        A class for SKASubarray's EndScan() command.
        """
        def __init__(self, target, state_model, logger=None):
            """
            Constructor for EndScanCommand

            :param target: the object that this command acts upon; for
                example, the SKASubarray device for which this class
                implements the command
            :type target: object
            :param state_model: the state model that this command uses
                 to check that it is allowed to run, and that it drives
                 with actions.
            :type state_model: SKABaseClassStateModel or a subclass of
                same
            :param logger: the logger to be used by this Command. If not
                provided, then a default module logger will be used.
            :type logger: a logger that implements the standard library
                logger interface
            """
            super().__init__(target, state_model, "end_scan", logger)

        def do(self, target, logger):
            """
            Stateless hook for EndScan() command functionality.

            :param target: the object that this command acts upon; for
                example, the SKASubarray device for which this class
                implements the command
            :type target: object
            :param logger: the logger for this Command.
            :type logger: a logger that implements the standard library
                logger interface
            :return: A tuple containing a return code and a string
                message indicating status. The message is for
                information purpose only.
            :rtype: (ReturnCode, str)
            """
            message = "EndScan command completed OK"
            logger.info(message)
            return (ReturnCode.OK, message)

    class EndCommand(ActionCommand):
        """
        A class for SKASubarray's End() command.
        """
        def __init__(self, target, state_model, logger=None):
            """
            Constructor for EndCommand

            :param target: the object that this command acts upon; for
                example, the SKASubarray device for which this class
                implements the command
            :type target: object
            :param state_model: the state model that this command uses
                 to check that it is allowed to run, and that it drives
                 with actions.
            :type state_model: SKABaseClassStateModel or a subclass of
                same
            :param logger: the logger to be used by this Command. If not
                provided, then a default module logger will be used.
            :type logger: a logger that implements the standard library
                logger interface
            """
            super().__init__(target, state_model, "end", logger)

        def do(self, target, logger):
            """
            Stateless hook for End() command functionality.

            :param target: the object that this command acts upon; for
                example, the SKASubarray device for which this class
                implements the command
            :type target: object
            :param logger: the logger for this Command.
            :type logger: a logger that implements the standard library
                logger interface
            :return: A tuple containing a return code and a string
                message indicating status. The message is for
                information purpose only.
            :rtype: (ReturnCode, str)
            """
            target._deconfigure()

            message = "End command completed OK"
            logger.info(message)
            return (ReturnCode.OK, message)

    class AbortCommand(DualActionCommand):
        """
        A class for SKASubarray's Abort() command.
        """
        def __init__(self, target, state_model, logger=None):
            """
            Constructor for AbortCommand

            :param target: the object that this command acts upon; for
                example, the SKASubarray device for which this class
                implements the command
            :type target: object
            :param state_model: the state model that this command uses
                 to check that it is allowed to run, and that it drives
                 with actions.
            :type state_model: SKABaseClassStateModel or a subclass of
                same
            :param logger: the logger to be used by this Command. If not
                provided, then a default module logger will be used.
            :type logger: a logger that implements the standard library
                logger interface
            """
            super().__init__(target, state_model, "abort", logger)

        def do(self, target, logger):
            """
            Stateless hook for Abort() command functionality.

            :param target: the object that this command acts upon; for
                example, the SKASubarray device for which this class
                implements the command
            :type target: object
            :param logger: the logger for this Command.
            :type logger: a logger that implements the standard library
                logger interface
            :return: A tuple containing a return code and a string
                message indicating status. The message is for
                information purpose only.
            :rtype: (ReturnCode, str)
            """
            message = "Abort command completed OK"
            logger.info(message)
            return (ReturnCode.OK, message)

    class ObsResetCommand(DualActionCommand):
        """
        A class for SKASubarray's ObsReset() command.
        """
        def __init__(self, target, state_model, logger=None):
            """
            Constructor for ObsResetCommand

            :param target: the object that this command acts upon; for
                example, the SKASubarray device for which this class
                implements the command
            :type target: object
            :param state_model: the state model that this command uses
                 to check that it is allowed to run, and that it drives
                 with actions.
            :type state_model: SKABaseClassStateModel or a subclass of
                same
            :param logger: the logger to be used by this Command. If not
                provided, then a default module logger will be used.
            :type logger: a logger that implements the standard library
                logger interface
            """
            super().__init__(target, state_model, "obs_reset", logger)

        def do(self, target, logger):
            """
            Stateless hook for ObsReset() command functionality.

            :param target: the object that this command acts upon; for
                example, the SKASubarray device for which this class
                implements the command
            :type target: object
            :param logger: the logger for this Command.
            :type logger: a logger that implements the standard library
                logger interface
            :return: A tuple containing a return code and a string
                message indicating status. The message is for
                information purpose only.
            :rtype: (ReturnCode, str)
            """
            # We might have interrupted a long-running command such as a Configure
            # or a Scan, so we need to clean up from that.

            # Now totally deconfigure
            target._deconfigure()

            message = "ObsReset command completed OK"
            logger.info(message)
            return (ReturnCode.OK, message)

    class RestartCommand(DualActionCommand):
        """
        A class for SKASubarray's Restart() command.
        """
        def __init__(self, target, state_model, logger=None):
            """
            Constructor for RestartCommand

            :param target: the object that this command acts upon; for
                example, the SKASubarray device for which this class
                implements the command
            :type target: object
            :param state_model: the state model that this command uses
                 to check that it is allowed to run, and that it drives
                 with actions.
            :type state_model: SKABaseClassStateModel or a subclass of
                same
            :param logger: the logger to be used by this Command. If not
                provided, then a default module logger will be used.
            :type logger: a logger that implements the standard library
                logger interface
            """
            super().__init__(target, state_model, "restart", logger)

        def do(self, target, logger):
            """
            Stateless hook for Restart() command functionality.

            :param target: the object that this command acts upon; for
                example, the SKASubarray device for which this class
                implements the command
            :type target: object
            :return: A tuple containing a return code and a string
                message indicating status. The message is for
                information purpose only.
            :rtype: (ReturnCode, str)
            """
            # We might have interrupted a long-running command such as a Configure
            # or a Scan, so we need to clean up from that.

            # Now totally deconfigure
            target._deconfigure()

            # and release all resources
            target._release_all_resources()

            message = "Restart command completed OK"
            logger.info(message)
            return (ReturnCode.OK, message)

    # PROTECTED REGION ID(SKASubarray.class_variable) ENABLED START #
    def _init_state_model(self):
        """
        Sets up the state model for the device
        """
        self.state_model = SKASubarrayStateModel(
            admin_mode_callback=self._update_admin_mode,
            state_callback=self._update_state,
            obs_state_callback=self._update_obs_state
        )

    def _init_command_objects(self):
        """
        Sets up the command objects
        """
        super()._init_command_objects()

        args = (self, self.state_model, self.logger)
        self._on_command = self.OnCommand(*args)
        self._off_command = self.OffCommand(*args)
        self._assign_resources_command = self.AssignResourcesCommand(*args)
        self._release_resources_command = self.ReleaseResourcesCommand(*args)
        self._release_all_resources_command = self.ReleaseAllResourcesCommand(
            *args
        )
        self._configure_command = self.ConfigureCommand(*args)
        self._scan_command = self.ScanCommand(*args)
        self._end_scan_command = self.EndScanCommand(*args)
        self._end_command = self.EndCommand(*args)
        self._abort_command = self.AbortCommand(*args)
        self._obs_reset_command = self.ObsResetCommand(*args)
        self._restart_command = self.RestartCommand(*args)

    def _assign_resources(self, resources):
        """
        Assign some resources

        :param resources: resources to assign
        :type resources: list of string
        """
        for resource in resources:
            if resource not in self._assigned_resources[:]:
                self._assigned_resources.append(resource)

    def _release_resources(self, resources):
        """
        Release some resources

        :param resources: resources to releae
        :type resources: list of string
        """
        for resource in resources:
            if resource in self._assigned_resources:
                self._assigned_resources.remove(resource)

    def _release_all_resources(self):
        """
        Release all resources
        """
        self._assigned_resources.clear()

    def is_resourced(self):
        """
        Whether this subarray has any resources

        :returns: whether this subarray has any resources
        :rtype: boolean
        """
        return self._assigned_resources

    def _validate_capability_types(self, capability_types):
        """
        Check the validity of the input parameter passed to the
        Configure command.

        :param device: the device for which this class implements
            the configure command
        :type device: SKASubarray
        :param capability_types: a list strings representing
            capability types.
        :type capability_types: list
        :raises ValueError: If any of the capabilities requested are
            not valid.
        """
        invalid_capabilities = list(
            set(capability_types) - set(self._configured_capabilities))

        if invalid_capabilities:
            raise CapabilityValidationError(
                "Invalid capability types requested {}".format(
                    invalid_capabilities
                )
            )

    def _deconfigure(self):
        """
        Completely deconfigure the subarray
        """
        self._configured_capabilities = {k: 0 for k in self._configured_capabilities}

    # -----------------
    # Device Properties
    # -----------------
    CapabilityTypes = device_property(
        dtype=('str',),
    )

    SubID = device_property(
        dtype='str',
    )

    # ----------
    # Attributes
    # ----------
    activationTime = attribute(
        dtype='double',
        unit="s",
        standard_unit="s",
        display_unit="s",
        doc="Time of activation in seconds since Unix epoch.",
    )

    assignedResources = attribute(
        dtype=('str',),
        max_dim_x=100,
        doc="The list of resources assigned to the subarray.",
    )

    configuredCapabilities = attribute(
        dtype=('str',),
        max_dim_x=10,
        doc="A list of capability types with no. of instances "
            "in use on this subarray; "
            "e.g.\nCorrelators:512, PssBeams:4, "
            "PstBeams:4, VlbiBeams:0.",
    )

    # ---------------
    # General methods
    # ---------------
    def always_executed_hook(self):
        # PROTECTED REGION ID(SKASubarray.always_executed_hook) ENABLED START #
        pass
        # PROTECTED REGION END #    //  SKASubarray.always_executed_hook

    def delete_device(self):
        # PROTECTED REGION ID(SKASubarray.delete_device) ENABLED START #
        pass
        # PROTECTED REGION END #    //  SKASubarray.delete_device

    # ------------------
    # Attributes methods
    # ------------------
    def read_activationTime(self):
        # PROTECTED REGION ID(SKASubarray.activationTime_read) ENABLED START #
        """
        Reads the time since device is activated.

        :return: Time of activation in seconds since Unix epoch.
        """
        return self._activation_time
        # PROTECTED REGION END #    //  SKASubarray.activationTime_read

    def read_assignedResources(self):
        # PROTECTED REGION ID(SKASubarray.assignedResources_read) ENABLED START #
        """
        Reads the resources assigned to the device.

        :return: Resources assigned to the device.
        """
        return self._assigned_resources
        # PROTECTED REGION END #    //  SKASubarray.assignedResources_read

    def read_configuredCapabilities(self):
        # PROTECTED REGION ID(SKASubarray.configuredCapabilities_read) ENABLED START #
        """
        Reads capabilities configured in the Subarray.

        :return: A list of capability types with no. of instances used
            in the Subarray
        """
        configured_capabilities = []
        for capability_type, capability_instances in (
                list(self._configured_capabilities.items())):
            configured_capabilities.append(
                "{}:{}".format(capability_type, capability_instances))
        return sorted(configured_capabilities)
        # PROTECTED REGION END #    //  SKASubarray.configuredCapabilities_read

    # --------
    # Commands
    # --------
    def is_On_allowed(self):
        """
        Check if command `On` is allowed in the current device state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return self._on_command.check_allowed()

    @command()
    @DebugIt()
    def On(self):
        """
        Turn subarray on
        """
        self._on_command()

    def is_Off_allowed(self):
        """
        Check if command `Off` is allowed in the current device state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return self._off_command.check_allowed()

    @command()
    @DebugIt()
    def Off(self):
        """
        Turn the subarray of
        """
        self._off_command()

    def is_AssignResources_allowed(self):
        """
        Check if command `AssignResources` is allowed in the current
        device state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return self._assign_resources_command.check_allowed()

    @command(
        dtype_in=('str',),
        doc_in="List of Resources to add to subarray.",
    )
    @DebugIt()
    def AssignResources(self, argin):
        """
        Assign resources to this subarray

        :param argin: the resources to be assigned
        :type argin: list of str
        """
        self._assign_resources_command(argin)

    def is_ReleaseResources_allowed(self):
        """
        Check if command `ReleaseResources` is allowed in the current
        device state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return self._release_resources_command.check_allowed()

    @command(
        dtype_in=('str',),
        doc_in="List of resources to remove from the subarray."
    )
    @DebugIt()
    def ReleaseResources(self, argin):
        """
        Delta removal of assigned resources.

        :param argin: the resources to be released
        :type argin: list of str
        """
        self._release_resources_command(argin)

    def is_ReleaseAllResources_allowed(self):
        """
        Check if command `ReleaseAllResources` is allowed in the current
        device state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return self._release_all_resources_command.check_allowed()

    @command()
    @DebugIt()
    def ReleaseAllResources(self):
        """
        Remove all resources to tear down to an empty subarray.

        :return: list of resources removed
        :rtype: list of string
        """
        self._release_all_resources_command()

    def is_Configure_allowed(self):
        """
        Check if command `Configure` is allowed in the current
        device state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return self._configure_command.check_allowed()

    @command(
        dtype_in='DevVarLongStringArray',
        doc_in="[Number of instances to add][Capability types]",
    )
    @DebugIt()
    def Configure(self, argin):
        """
        Configures the capabilities of this subarray

        :param argin: configuration specification
        :type argin: string
        """
        self._configure_command(argin)

    def is_Scan_allowed(self):
        """
        Check if command `Scan` is allowed in the current device state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return self._scan_command.check_allowed()

    @command(dtype_in=('str',),)
    @DebugIt()
    def Scan(self, argin):
        """
        Start scanning

        :param argin: Information about the scan
        :type argin: Array of str
        """
        self._scan_command(argin)

    def is_EndScan_allowed(self):
        """
        Check if command `EndScan` is allowed in the current device state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return self._end_scan_command.check_allowed()

    @command()
    @DebugIt()
    def EndScan(self):
        """
        End the scan
        """
        self._end_scan_command()

    def is_End_allowed(self):
        """
        Check if command `End` is allowed in the current device state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return self._end_command.check_allowed()

    @command()
    @DebugIt()
    def End(self):
        # PROTECTED REGION ID(SKASubarray.EndSB) ENABLED START #
        """
        End the scan block.
        """
        self._end_command()

    def is_Abort_allowed(self):
        """
        Check if command `Abort` is allowed in the current device state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return self._abort_command.check_allowed()

    @command()
    @DebugIt()
    def Abort(self):
        """
        Abort any long-running command such as ``Configure()`` or
        ``Scan()``.
        """
        self._abort_command()

    def is_ObsReset_allowed(self):
        """
        Check if command `ObsReset` is allowed in the current device
        state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return self._obs_reset_command.check_allowed()

    @command()
    @DebugIt()
    def ObsReset(self):
        """
        Reset the current observation process.
        """
        self._obs_reset_command()

    def is_Restart_allowed(self):
        """
        Check if command `Restart` is allowed in the current device
        state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return self._restart_command.check_allowed()

    @command()
    @DebugIt()
    def Restart(self):
        """
        Restart the subarray. That is, deconfigure and release
        all resources.
        """
        self._restart_command()


# ----------
# Run server
# ----------
def main(args=None, **kwargs):
    # PROTECTED REGION ID(SKASubarray.main) ENABLED START #
    """
    Main entry point of the module.
    """
    return run((SKASubarray,), args=args, **kwargs)
    # PROTECTED REGION END #    //  SKASubarray.main


if __name__ == '__main__':
    main()
