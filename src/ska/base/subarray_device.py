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
from tango import AttrWriteType, DevState, Except, ErrSeverity
from tango.server import run, attribute, command
from tango.server import device_property

# SKA specific imports
from ska.base import SKAObsDevice, SKAObsDeviceStateModel
from ska.base.control_model import ObsState, ReturnCode, check_first, guard, DevFailed_if_False
# PROTECTED REGION END #    //  SKASubarray.additionnal_imports

__all__ = ["SKASubarray", "SKASubarrayStateModel", "main"]


class SKASubarrayStateModel(SKAObsDeviceStateModel):
    """
    Implements the state model for the SKASubarray
    """
    def is_on_allowed(self):
        return guard.allows(
            self,
            state=DevState.OFF,
        )

    @check_first("on")
    def on_succeeded(self):
        """
        Method that manages device state in response to completion of
        the `On` command.
        """
        self._set_state(DevState.ON)
        self._obs_state = ObsState.EMPTY

    @check_first("on")
    def on_failed(self):
        self._set_state(DevState.FAULT)

    def is_off_allowed(self):
        return guard.allows(
            self,
            state=DevState.ON,
            obs_state=ObsState.EMPTY
        )

    @check_first("off")
    def off_succeeded(self):
        """
        Method that manages device state in response to completion of
        the `Off` command.
        """
        self._set_state(DevState.OFF)

    @check_first("off")
    def off_failed(self):
        self._set_state(DevState.FAULT)

    def is_assign_started_allowed(self):
        """
        Check if command `AssignResources` is allowed in the current
        device state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return guard.allows(
            self,
            is_obs=[ObsState.EMPTY, ObsState.IDLE]
        )

    def _resourcing_started(self):
        self._obs_state = ObsState.RESOURCING

    @check_first()
    def assign_started(self):
        self._resourcing_started()

    def _is_resourcing_completed_allowed(self):
        return guard.allows(self, is_obs=[ObsState.RESOURCING])

    def is_assign_completed_allowed(self):
        return self._is_resourcing_completed_allowed()

    def _resourcing_succeeded_no_resources(self):
        self._obs_state = ObsState.EMPTY

    @check_first("assign_completed")
    def assign_succeeded_no_resources(self):
        self._resourcing_succeeded_no_resources()

    def _resourcing_succeeded_some_resources(self):
        self._obs_state = ObsState.IDLE

    @check_first("assign_completed")
    def assign_succeeded_some_resources(self):
        self._resourcing_succeeded_some_resources()

    @check_first("assign_completed")
    def assign_failed(self):
        self._obs_state = ObsState.FAULT

    def is_release_started_allowed(self):
        return guard.allows(self, is_obs=[ObsState.IDLE])

    @check_first()
    def release_started(self):
        self._resourcing_started()

    def is_release_completed_allowed(self):
        return self._is_resourcing_completed_allowed()

    @check_first("release_completed")
    def release_succeeded_no_resources(self):
        self._resourcing_succeeded_no_resources()

    @check_first("release_completed")
    def release_succeeded_has_resources(self):
        self._resourcing_succeeded_some_resources()

    @check_first("release_completed")
    def release_failed(self):
        self._obs_state = ObsState.FAULT

    def is_configure_started_allowed(self):
        return guard.allows(
            self,
            is_obs=[ObsState.IDLE, ObsState.READY]
        )

    @check_first()
    def configure_started(self):
        self._obs_state = ObsState.CONFIGURING

    def is_configure_completed_allowed(self):
        return guard.allows(self, is_obs=[ObsState.CONFIGURING])

    @check_first("configure_completed")
    def configure_succeeded(self):
        self._obs_state = ObsState.READY

    @check_first("configure_completed")
    def configure_failed(self):
        self._obs_state = ObsState.FAULT

    def is_scan_started_allowed(self):
        return guard.allows(self, is_obs=[ObsState.READY])

    @check_first()
    def scan_started(self):
        self._obs_state = ObsState.SCANNING

    def is_scan_completed_allowed(self):
        return guard.allows(self, is_obs=[ObsState.SCANNING])

    @check_first("scan_completed")
    def scan_succeeded(self):
        self._obs_state = ObsState.READY

    @check_first("scan_completed")
    def scan_failed(self):
        self._obs_state = ObsState.FAULT

    def is_end_scan_allowed(self):
        return guard.allows(self, is_obs=[ObsState.SCANNING])

    @check_first("end_scan")
    def end_scan_succeeded(self):
        self._obs_state = ObsState.READY

    @check_first("end_scan")
    def end_scan_failed(self):
        self._obs_state = ObsState.FAULT

    def is_end_allowed(self):
        return guard.allows(self, is_obs=[ObsState.READY])

    @check_first("end")
    def end_succeeded(self):
        self._obs_state = ObsState.IDLE

    @check_first("scan_completed")
    def end_failed(self):
        self._obs_state = ObsState.FAULT

    def is_abort_allowed(self):
        return guard.allows(
            self,
            is_obs=[ObsState.IDLE, ObsState.CONFIGURING, ObsState.READY,
                    ObsState.SCANNING, ObsState.RESETTING]
        )

    @check_first("abort")
    def abort_succeeded(self):
        self._obs_state = ObsState.ABORTED

    @check_first("abort")
    def abort_failed(self):
        self._obs_state = ObsState.FAULT


#    def is_reset_started_allowed(self):
#        return guard.allows(self, is_obs=[ObsState.ABORTED, ObsState.FAULT])

    @check_first()
    def obs_reset_started(self):
        self._obs_state = ObsState.RESETTING

    def is_obs_reset_completed_allowed(self):
        return guard.allows(
            self,
            is_obs=[ObsState.RESETTING]
        )

    @check_first("obs_reset_completed")
    def obs_reset_succeeded(self):
        self._obs_state = ObsState.IDLE

    @check_first("obs_reset_completed")
    def obs_reset_failed(self):
        self._obs_state = ObsState.FAULT

    def is_restart_started_allowed(self):
        return guard.allows(
            self,
            is_obs=[ObsState.ABORTED, ObsState.FAULT]
        )

    @check_first()
    def restart_started(self):
        self._obs_state = ObsState.RESTARTING

    def is_restart_completed_allowed(self):
        return guard.allows(
            self,
            is_obs=[ObsState.RESTARTING]
        )

    @check_first("restart_completed")
    def restart_succeeded(self):
        self._obs_state = ObsState.EMPTY

    @check_first("restart_completed")
    def restart_failed(self):
        self._obs_state = ObsState.FAULT

    @check_first()
    def to_fault(self):
        # override to support ObsState.FAULT
        if self._state == DevState.ON:
            self._obs_state = ObsState.FAULT
        else:
            self._set_state(DevState.FAULT)


class SKASubarray(SKAObsDevice):
    """
    SubArray device
    """
    state_model_class = SKASubarrayStateModel

    # PROTECTED REGION ID(SKASubarray.class_variable) ENABLED START #
    def _validate_capability_types(self, command_name, capability_types):
        """Check the validity of the input parameter passed on to the command specified
        by the command_name parameter.

        Parameters
        ----------
        command_name: str
            The name of the command which is to be executed.
        capability_types: list
            A list strings representing capability types.

        Raises
        ------
        tango.DevFailed: If any of the capabilities requested are not valid.
        """
        invalid_capabilities = list(
            set(capability_types) - set(self._configured_capabilities))

        if invalid_capabilities:
            Except.throw_exception(
                "Command failed!", "Invalid capability types requested {}".format(
                    invalid_capabilities), command_name, ErrSeverity.ERR)

    def _validate_input_sizes(self, command_name, argin):
        """Check the validity of the input parameters passed on to the command specified
        by the command_name parameter.

        Parameters
        ----------
        command_name: str
            The name of the command which is to be executed.
        argin: tango.DevVarLongStringArray
            A tuple of two lists representing [number of instances][capability types]

        Raises
        ------
        tango.DevFailed: If the two lists are not equal in length.
        """
        capabilities_instances, capability_types = argin
        if len(capabilities_instances) != len(capability_types):
            Except.throw_exception(
                "Command failed!", "Argin value lists size mismatch.",
                command_name, ErrSeverity.ERR
            )

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
    def do_init_device(self):
        """
        Stateless hook for implementation of ``init_device()``.
        Subclasses that have no need to override the default
        implementation of state management may leave ``init_device()``
        alone and override this method instead.

        :return: A tuple containing a return code and a string message
            indicating status. The message is for information purpose
            only.
        :rtype: (ReturnCode, str)
        """
        (return_code, message) = super().do_init_device()

        # Initialize attribute values.
        self._activation_time = 0.0
        self._assigned_resources = [""]
        self._assigned_resources.clear()
        # self._configured_capabilities is gonna be kept as a dictionary internally. The
        # keys and value will represent the capability type name and the number of
        # instances, respectively.
        try:
            self._configured_capabilities = dict.fromkeys(self.CapabilityTypes, 0)
        except TypeError:
            # Might need to have the device property be mandatory in the database.
            self._configured_capabilities = {}

        return (return_code, message)

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

    @DevFailed_if_False
    def is_On_allowed(self):
        """
        Check if command `On` is allowed in the current device state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return self.state_model.is_on_allowed()

    @command()
    @DebugIt()
    def On(self):
        """
        Turn subarray on

        :note: Subclasses that implement this functionality are
            recommended to leave this command as currently implemented,
            and instead override the stateless hook ``do_On()``.
        """
        self._call_with_pattern("on")

    def do_On(self):
        """
        Stateless hook for implementation of ``On()`` command.
        Subclasses that have no need to override the default
        implementation of state management may leave ``On()`` alone and
        override this method instead.

        :return: A tuple containing a return code and a string message
            indicating status. The message is for information purpose
            only.
        :rtype: (ReturnCode, str)
        """
        return (ReturnCode.OK, "On command successful")

    @DevFailed_if_False
    def is_Off_allowed(self):
        """
        Check if command `Off` is allowed in the current device state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return self.state_model.is_off_allowed()

    @command()
    @DebugIt()
    def Off(self):
        """
        Turn subarray off

        :note: Subclasses that implement this functionality are
            recommended to leave this command as currently implemented,
            and instead override the stateless hook ``do_Off()``.
        """
        self._call_with_pattern("off")

    def do_Off(self):
        """
        Stateless hook for implementation of ``Off()`` command.
        Subclasses that have no need to override the default
        implementation of state management may leave ``Off()`` alone and
        override this method instead.

        :return: A tuple containing a return code and a string message
            indicating status. The message is for information purpose
            only.
        :rtype: (ReturnCode, str)
        """
        return (ReturnCode.OK, "Off command successful")

    @DevFailed_if_False
    def is_AssignResources_allowed(self):
        """
        Check if command `AssignResources` is allowed in the current
        device state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return self.state_model.is_assign_started_allowed()

    @command(dtype_in=('str',), doc_in="List of Resources to add to subarray.")
    @DebugIt()
    def AssignResources(self, argin):
        """
        Assign resources to a subarray.

        :note: Subclasses that implement this functionality are
            recommended to leave this command as currently implemented,
            and instead override the stateless hook
            ``do_AssignResources()``.
        """
        # Technical debt: can't use _call_with_pattern here because the
        # pattern doesn't allow for device-dependent decision on what
        # state model method to call. Should be fixed in pytransitions
        # refactor
        try:
            if self.state_model.assign_started is not None:
                self.state_model.assign_started()

            (return_code, message) = self.do_AssignResources(argin)

            if return_code == ReturnCode.OK:
                self.action_on_resourcing_succeeded()
            elif return_code == ReturnCode.FAILED:
                if self.state_model.assign_failed is not None:
                    self.state_model.assign_failed()
                else:
                    self.state_model.to_fault()
        except Exception:
            self.state_model.to_fault()
            raise

    def action_on_resourcing_succeeded(self):
        if self.is_resourced():
            self.state_model.assign_succeeded_has_resources()
        else:
            self.state_model.assign_succeeded_no_resources()

    def do_AssignResources(self, argin):
        """
        Stateless hook for implementation of ``AssignResources()``
        command. Subclasses that have no need to override the default
        implementation of state management may leave
        ``AssignResources()`` alone and override this method instead.

        :param argin: The resources to be assigned
        :type argin: list of str
        :return: A tuple containing a return code and a string message
            indicating status. The message is for information purpose
            only.
        :rtype: (ReturnCode, str)
        """
        resources = self._assigned_resources[:]
        for resource in argin:
            if resource not in resources:
                self._assigned_resources.append(resource)
        return (ReturnCode.OK, "Resources assigned")

    def is_resourced(self):
        return self._assigned_resources

    @DevFailed_if_False
    def is_ReleaseResources_allowed(self):
        """
        Check if command `ReleaseResources` is allowed in the current
        device state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return self.state_model.is_release_started_allowed()

    @command(
        dtype_in=('str',),
        doc_in="List of resources to remove from the subarray."
    )
    @DebugIt()
    def ReleaseResources(self, argin):
        """
        Delta removal of assigned resources.

        :note: Subclasses that implement this functionality are
            recommended to leave this command as currently implemented,
            and instead override the stateless hook
            ``do_ReleaseResources()``.
        :param argin: the resources to be released
        :type argin: list of str
        """
        # Technical debt: can't use _call_with_pattern here because the
        # pattern doesn't allow for device-dependent decision on what
        # state model method to call. Should be fixed in pytransitions
        # refactor
        try:
            if self.state_model.release_started is not None:
                self.state_model.release_started()

            (return_code, message) = self.do_ReleaseResources(argin)

            if return_code == ReturnCode.OK:
                self.action_on_resourcing_succeeded()
            elif return_code == ReturnCode.FAILED:
                if self.state_model.release_failed is not None:
                    self.state_model.release_failed()
                else:
                    self.state_model.to_fault()
        except Exception:
            self.state_model.to_fault()
            raise

    def do_ReleaseResources(self, argin):
        """
        Stateless hook for implementation of ``ReleaseResources()``
        command. Subclasses that have no need to override the default
        implementation of state management may leave
        ``ReleaseResources()`` alone and override this method instead.

        :param argin: the resources to be released
        :type argin: list of str
        :return: A tuple containing a return code and a string message
            indicating status. The message is for information purpose
            only.
        :rtype: (ReturnCode, str)
        """
        resources = self._assigned_resources[:]
        for resource in argin:
            if resource in resources:
                self._assigned_resources.remove(resource)
        return (ReturnCode.OK, "Resources released")

    @DevFailed_if_False
    def is_ReleaseAllResources_allowed(self):
        """
        Check if command `ReleaseAllResources` is allowed in the current
        device state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return self.state_model.is_release_started_allowed()

    @command()
    @DebugIt()
    def ReleaseAllResources(self):
        """
        Remove all resources to tear down to an empty subarray.

        :note: Subclasses that implement this functionality are
            recommended to leave this command as currently implemented,
            and instead override the stateless hook
            ``do_ReleaseAllResources()``.
        :return: list of resources removed
        :rtype: list of string
        """
        # Technical debt: can't use _call_with_pattern here because the
        # pattern doesn't allow for device-dependent decision on what
        # state model method to call. Should be fixed in pytransitions
        # refactor
        try:
            if self.state_model.release_started is not None:
                self.state_model.release_started()

            (return_code, message) = self.do_ReleaseAllResources()

            if return_code == ReturnCode.OK:
                self.state_model.release_succeeded_no_resources()
            elif return_code == ReturnCode.FAILED:
                if self.state_model.release_failed is not None:
                    self.state_model.release_failed()
                else:
                    self.state_model.to_fault()
        except Exception:
            self.state_model.to_fault()
            raise

    def do_ReleaseAllResources(self):
        """
        Stateless hook for implementation of ``ReleaseAllResources()``
        command. Subclasses that have no need to override the default
        implementation of state management may leave
        ``ReleaseAllResources()`` alone and override this method instead.

        :return: A tuple containing a return code and a string message
            indicating status. The message is for information purpose
            only.
        :rtype: (ReturnCode, str)
        """
        resources = self._assigned_resources[:]
        return self.do_ReleaseResources(resources)

    @DevFailed_if_False
    def is_Configure_allowed(self):
        """
        Check if command `Configure` is allowed in the current
        device state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return self.state_model.is_configure_started_allowed()

    @command(
        dtype_in='DevVarLongStringArray',
        doc_in="[Number of instances to add][Capability types]",
    )
    @DebugIt()
    def Configure(self, argin):
        """
        Configures the capabilities of this subarray

        :note: Subclasses that implement this functionality are
            recommended to leave this command as currently implemented,
            and instead override the stateless hook
            ``do_Configure()``.
        :param argin: configuration specification
        :type argin: string
        """
        self._call_with_pattern("configure", argin)

    def do_Configure(self, argin):
        """
        Stateless hook for implementation of ``Configure()`` command.
        Subclasses that have no need to override the default
        implementation of state management may leave ``Configure()``
        alone and override this method instead.

        :param argin: configuration specification
        :type argin: str
        :return: A tuple containing a return code and a string message
            indicating status. The message is for information purpose
            only.
        :rtype: (ReturnCode, str)
        """
        command_name="Configure"
        capabilities_instances, capability_types = argin
        self._validate_capability_types(command_name, capability_types)
        self._validate_input_sizes(command_name, argin)

        # Perform the configuration.
        for capability_instances, capability_type in zip(
                capabilities_instances, capability_types):
            self._configured_capabilities[capability_type] += capability_instances

        return (ReturnCode.OK, "Capability configured")

    def _deconfigure(self):
        self._configured_capabilities = {k:0 for k in self._configured_capabilities}

    @DevFailed_if_False
    def is_Scan_allowed(self):
        """
        Check if command `Scan` is allowed in the current device state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return self.state_model.is_scan_started_allowed()

    @command(dtype_in=('str',),)
    @DebugIt()
    def Scan(self, argin):
        """
        Start scanning

        :note: Subclasses that implement this functionality are
            recommended to leave this command as currently implemented,
            and instead override the stateless hook
            ``do_Scan()``.
        :param argin: Information about the scan
        :type argin: Array of str
        """
        self._call_with_pattern("scan", argin)

    def do_Scan(self, argin):
        """
        Stateless hook for implementation of ``Scan()`` command.
        Subclasses that have no need to override the default
        implementation of state management may leave ``Scan()`` alone
        and override this method instead.

        :param argin: Information about the scan
        :type argin: Array of str
        :return: A tuple containing a return code and a string message
            indicating status. The message is for information purpose
            only.
        :rtype: (ReturnCode, str)
        """
        # For testing purposes, in this synchronous version of the code,
        # we won't let the scan complete synchronously; we'll force the
        # device to remain in SCANNING mode until we interrupt it e.g.
        # with EndScan() or Abort().
        return (ReturnCode.STARTED, "Scan started")

    @DevFailed_if_False
    def is_EndScan_allowed(self):
        """
        Check if command `EndScan` is allowed in the current device state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return self.state_model.is_scan_completed_allowed()

    @command()
    @DebugIt()
    def EndScan(self):
        """
        End the scan

        :note: Subclasses that implement this functionality are
            recommended to leave this command as currently implemented,
            and instead override the stateless hook
            ``do_EndScan()``.
        """
        self._call_with_pattern("end_scan")

    def do_EndScan(self):
        """
        Stateless hook for implementation of ``EndScan()`` command.
        Subclasses that have no need to override the default
        implementation of state management may leave ``EndScan()`` alone
        and override this method instead.

        :return: A tuple containing a return code and a string message
            indicating status. The message is for information purpose
            only.
        :rtype: (ReturnCode, str)
        """
        return (ReturnCode.OK, "EndScan command successful")

    @DevFailed_if_False
    def is_End_allowed(self):
        """
        Check if command `End` is allowed in the current device state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return self.state_model.is_end_allowed()

    @command(
    )
    @DebugIt()
    def End(self):
        # PROTECTED REGION ID(SKASubarray.EndSB) ENABLED START #
        """
        End the scan block.

        :note: Subclasses that implement this functionality are
            recommended to leave this command as currently implemented,
            and instead override the stateless hook
            ``do_End()``.
        """
        self._call_with_pattern("end")

    def do_End(self):
        """
        Stateless hook for implementation of ``End()`` command.
        Subclasses that have no need to override the default
        implementation of state management may leave ``End()`` alone
        and override this method instead.

        :return: A tuple containing a return code and a string message
            indicating status. The message is for information purpose
            only.
        :rtype: (ReturnCode, str)
        """
        self._deconfigure()
        return (ReturnCode.OK, "End successful")

    @DevFailed_if_False
    def is_Abort_allowed(self):
        """
        Check if command `Abort` is allowed in the current device state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return self.state_model.is_abort_allowed()

    @command()
    @DebugIt()
    def Abort(self):
        """
        Abort any long-running command such as ``Configure()`` or
        ``Scan()``.

        :note: Subclasses that implement this functionality are
            recommended to leave this command as currently implemented,
            and instead override the stateless hook
            ``do_Abort()``.
        """
        self._call_with_pattern("abort")

    def do_Abort(self):
        """
        Stateless hook for implementation of ``Abort()`` command.
        Subclasses that have no need to override the default
        implementation of state management may leave ``Abort()`` alone
        and override this method instead.

        :return: A tuple containing a return code and a string message
            indicating status. The message is for information purpose
            only.
        :rtype: (ReturnCode, str)
        """
        # Here we should stop any current running configuring or scan.
        return (ReturnCode.OK, "Abort command successful")

    @DevFailed_if_False
    def is_Reset_allowed(self):
        """
        Check if command `Reset` is allowed in the current device state.

        This command has a special semantics for subarrays: it is
        permitted only in the ABORTED ObsState, and serves to get the
        subarray back to the state of being resourced but unconfigured.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return self.state_model.is_reset_allowed()

    @command()
    @DebugIt()
    def Reset(self):
        """
        Reset the subarray.

        This command has a special semantics for subarrays: it is
        essentially passed through to the nested observation state
        machine, and resets that, rather than the subarray itself. That
        is: the subarray stops any ongoing observation activity,
        and deconfigures, but it does NOT release its resources or
        change device state. Thus it only makes sense for
        an enabled, online, resourced subarray.

        :note: Subclasses that implement this functionality are
            recommended to leave this command as currently implemented,
            and instead override the stateless hook
            ``do_Reset()``.
        """
        self._call_with_pattern("reset")

    def do_Reset(self):
        """
        Stateless hook for implementation of ``Reset()`` command.
        Subclasses that have no need to override the default
        implementation of state management may leave ``Reset()`` alone
        and override this method instead.

        :return: A tuple containing a return code and a string message
            indicating status. The message is for information purpose
            only.
        :rtype: (ReturnCode, str)
        """
        # Don't call superclass command because this command has a completely
        # different semantics for subarrays.

        # We might have interrupted a long-running command such as a Configure
        # or a Scan, so we need to clean up from that.
        pass

        # Now totally deconfigure
        self._deconfigure()
        return (ReturnCode.OK, "Reset successful")

    @DevFailed_if_False
    def is_Restart_allowed(self):
        """
        Check if command `Restart` is allowed in the current device
        state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return self.state_model.is_restart_allowed()

    @command()
    @DebugIt()
    def Restart(self):
        """
        Restart the subarray. That is, deconfigure and release
        all resources.

        :note: Subclasses that implement this functionality are
            recommended to leave this command as currently implemented,
            and instead override the stateless hook
            ``do_Restart()``.
        """
        self._call_with_pattern("restart")

    def do_Restart(self):
        """
        Stateless hook for implementation of ``Restart()`` command.
        Subclasses that have no need to override the default
        implementation of state management may leave ``Restart()`` alone
        and override this method instead.

        :return: A tuple containing a return code and a string message
            indicating status. The message is for information purpose
            only.
        :rtype: (ReturnCode, str)
        """
        # We might have interrupted a long-running command such as a Configure
        # or a Scan, so we need to clean up from that.
        pass

        # Now totally deconfigure
        self._deconfigure()

        # and release all resources
        self.do_ReleaseAllResources()

        return (ReturnCode.OK, "Reset successful")

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
