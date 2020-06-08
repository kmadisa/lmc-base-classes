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
from ska.base import SKAObsDevice
from ska.base.control_model import AdminMode, ObsState, ReturnCode, guard
# PROTECTED REGION END #    //  SKASubarray.additionnal_imports

__all__ = ["SKASubarray", "main"]


class SKASubarray(SKAObsDevice):
    """
    SubArray device
    """
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
            Except.throw_exception("Command failed!", "Argin value lists size mismatch.",
                                   command_name, ErrSeverity.ERR)

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

    # overriding base class because this is not memorized for subarrays
    adminMode = attribute(
        dtype=AdminMode,
        access=AttrWriteType.READ_WRITE,
        doc="The admin mode reported for this device. It may interpret the current "
            "device condition and condition of all managed devices to set this. "
            "Most possibly an aggregate attribute.",
    )

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

    def init_device_requested(self):
        """
        Method that manages device state in response to `init_device`
        command being invoked.
        """
        super().init_device_requested()

        # Subarrays are logical devices, and a pool of them is created
        # at start-up, to be put online and used as needed, Therefore
        # the subarray adminMode is initialised into adminMode OFFLINE,
        # and is NOT memorized.
        self._admin_mode = AdminMode.OFFLINE

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

    def is_AssignResources_allowed(self):
        """
        Check if command `AssignResources` is allowed in the current
        device state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return guard.require(
            self,
            "is_AssignResources_allowed",
            admin_modes=[AdminMode.ONLINE, AdminMode.MAINTENANCE],
            states=[DevState.OFF, DevState.ON],
            obs_states=[ObsState.IDLE]
        )

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
        self._call_with_pattern(argin)

    def AssignResources_requested(self):
        """
        Method that manages device state in response to
        `AssignResources` command being invoked.
        """
        pass

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

    def AssignResources_completed(self, return_code):
        """
        Method that manages device state in response to completion of
        the `AssignResources` command.
        """
        if self.is_resourced():
            self.set_state(DevState.ON)
            self.set_status("The device is in ON state.")
        else:
            self.set_state(DevState.OFF)
            self.set_status("The device is in OFF state.")

    def is_resourced(self):
        return self._assigned_resources

    def is_ReleaseResources_allowed(self):
        """
        Check if command `ReleaseResources` is allowed in the current
        device state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return guard.require(self, "is_ReleaseResources_allowed",
                             is_obs=[ObsState.IDLE])

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
        return self._call_with_pattern(argin)

    def ReleaseResources_requested(self):
        """
        Method that manages device state in response to
        `ReleaseResources` command being invoked.
        """
        pass

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

    def ReleaseResources_completed(self, return_code):
        """
        Method that manages device state in response to completion of
        the `ReleaseResources` command.
        """
        if self.is_resourced():
            self.set_state(DevState.ON)
            self.set_status("The device is in ON state.")
        else:
            self.set_state(DevState.OFF)
            self.set_status("The device is in OFF state.")

    def is_ReleaseAllResources_allowed(self):
        """
        Check if command `ReleaseAllResources` is allowed in the current
        device state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return guard.require(self, "is_ReleaseAllResources_allowed",
                             is_obs=[ObsState.IDLE])

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
        self._call_with_pattern()

    def ReleaseAllResources_requested(self):
        """
        Method that manages device state in response to
        `ReleaseAllResources` command being invoked.
        """
        pass

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

    def ReleaseAllResources_completed(self, return_code):
        """
        Method that manages device state in response to completion of
        the `ReleaseAllResources` command.
        """
        self.set_state(DevState.OFF)
        self.set_status("The device is in OFF state.")

    def is_ConfigureCapability_allowed(self):
        """
        Check if command `ConfigureCapability` is allowed in the current
        device state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return guard.require(self, "is_ConfigureCapability_allowed",
                             is_obs=[ObsState.IDLE, ObsState.READY])

    @command(
        dtype_in='DevVarLongStringArray',
        doc_in="[Number of instances to add][Capability types]",
    )
    @DebugIt()
    def ConfigureCapability(self, argin):
        """
        Configures the capabilities of this subarray

        :note: Subclasses that implement this functionality are
            recommended to leave this command as currently implemented,
            and instead override the stateless hook
            ``do_ConfigureCapability()``.
        :param argin: configuration specification
        :type argin: string
        """
        self._call_with_pattern(argin)

    def ConfigureCapability_requested(self):
        """
        Method that manages device state in response to
        `ConfigureCapability` command being invoked.
        """
        self._obs_state = ObsState.CONFIGURING

    def do_ConfigureCapability(self, argin):
        """
        Stateless hook for implementation of ``ConfigureCapability()``
        command. Subclasses that have no need to override the default
        implementation of state management may leave
        ``ConfigureCapability()`` alone and override this method instead.

        :param argin: configuration specification
        :type argin: str
        :return: A tuple containing a return code and a string message
            indicating status. The message is for information purpose
            only.
        :rtype: (ReturnCode, str)
        """
        command_name = 'ConfigureCapability'

        capabilities_instances, capability_types = argin
        self._validate_capability_types(command_name, capability_types)
        self._validate_input_sizes(command_name, argin)

        # Perform the configuration.
        for capability_instances, capability_type in zip(
                capabilities_instances, capability_types):
            self._configured_capabilities[capability_type] += capability_instances

        return (ReturnCode.OK, "Capability configured")

    @guard(is_obs=[ObsState.CONFIGURING])
    def ConfigureCapability_completed(self, return_code):
        """
        Method that manages device state in response to completion of
        the `ConfigureCapability` command.
        """
        if self.is_configured():
            self._obs_state = ObsState.READY
        else:
            self._obs_state = ObsState.IDLE

    def is_configured(self):
        """
        Checks if this subarray has any configured capabilities at all.

        :return: whether this subarray has any configured capabilities.
        :rtype: boolean
        """
        return any(self._configured_capabilities.values())

    def is_DeconfigureAllCapabilities_allowed(self):
        """
        Check if command `DeconfigureAllCapabilities` is allowed in the
        current device state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return guard.require(self, "is_DeconfigureAllCapabilities_allowed",
                             is_obs=[ObsState.READY])

    @command(dtype_in='str', doc_in="Capability type",)
    @DebugIt()
    def DeconfigureAllCapabilities(self, argin):
        """
        Deconfigure all instances of the given Capability type.

        :param argin: the name of the capability type, all instances of
            which are to be deconfigured
        :type argin: str
        :note: Subclasses that implement this functionality are
            recommended to leave this command as currently implemented,
            and instead override the stateless hook
            ``do_DeconfigureAllCapabilities()``.
        """
        self._call_with_pattern(argin)

    def DeconfigureAllCapabilities_requested(self):
        """
        Method that manages device state in response to
        `DeconfigureAllCapabilities` command being invoked.
        """
        self._obs_state = ObsState.CONFIGURING

    def do_DeconfigureAllCapabilities(self, argin):
        """
        Stateless hook for implementation of
        ``DeconfigureAllCapabilities()`` command. Subclasses that have
        no need to override the default implementation of state
        management may leave ``DeconfigureAllCapabilities()`` alone and
        override this method instead.

        :param argin: the name of the capability type, all instances of
            which are to be deconfigured
        :type argin: str
        :return: A tuple containing a return code and a string message
            indicating status. The message is for information purpose
            only.
        :rtype: (ReturnCode, str)
        """
        self._validate_capability_types('DeconfigureAllCapabilities', [argin])
        self._configured_capabilities[argin] = 0
        return (ReturnCode.OK, "Deconfiguration successful.")

    def DeconfigureAllCapabilities_completed(self, return_code):
        """
        Method that manages device state in response to completion of
        the `DeconfigureAllCapabilities` command.
        """
        if self.is_configured():
            self._obs_state = ObsState.READY
        else:
            self._obs_state = ObsState.IDLE

    def is_DeconfigureCapability_allowed(self):
        """
        Check if command `DeconfigureCapability` is allowed in the
        current device state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return guard.require(self, "is_DeconfigureCapability_allowed",
                             is_obs=[ObsState.READY])

    @command(
        dtype_in='DevVarLongStringArray',
        doc_in="[Number of instances to remove][Capability types]",
    )
    @DebugIt()
    def DeconfigureCapability(self, argin):
        """
        Deconfigure some instances of a Capability type.

        :param argin: the capability type and the number of instances of
            that type to be removed, in array form: [no_instances][type]
        :type argin: DevVarLongStringArray
        :note: Subclasses that implement this functionality are
            recommended to leave this command as currently implemented,
            and instead override the stateless hook
            ``do_DeconfigureCapabilities()``.
        """
        self._call_with_pattern(argin)

    def DeconfigureCapability_requested(self):
        """
        Method that manages device state in response to
        `DeconfigureCapability` command being invoked.
        """
        self._obs_state = ObsState.CONFIGURING

    def do_DeconfigureCapability(self, argin):
        """
        Stateless hook for implementation of
        ``DeconfigureCapability()`` command. Subclasses that have no
        need to override the default implementation of state
        management may leave ``DeconfigureCapability()`` alone and
        override this method instead.

        :param argin: the name of the capability type, all instances of
            which are to be deconfigured
        :type argin: str
        :return: A tuple containing a return code and a string message
            indicating status. The message is for information purpose
            only.
        :rtype: (ReturnCode, str)
        """
        command_name = 'DeconfigureCapability'
        capabilities_instances, capability_types = argin

        self._validate_capability_types(command_name, capability_types)
        self._validate_input_sizes(command_name, argin)

        # Perform the deconfiguration
        for capability_instances, capability_type in zip(
                capabilities_instances, capability_types):
            if self._configured_capabilities[capability_type] < int(capability_instances):
                self._configured_capabilities[capability_type] = 0
            else:
                self._configured_capabilities[capability_type] -= (
                    int(capability_instances))
        return (ReturnCode.OK, "DeconfigureCapability command successful")

    def DeconfigureCapability_completed(self, return_code):
        """
        Method that manages device state in response to completion of
        the `DeconfigureCapability` command.
        """
        if self.is_configured():
            self._obs_state = ObsState.READY
        else:
            self._obs_state = ObsState.IDLE

    def is_Scan_allowed(self):
        """
        Check if command `Scan` is allowed in the current device state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return guard.require(self, "is_Scan_allowed",
                             is_obs=[ObsState.READY])

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
        self._call_with_pattern(argin)

    def Scan_requested(self):
        """
        Method that manages device state in response to `Scan` command
        being invoked.
        """
        self._obs_state = ObsState.SCANNING

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

    @guard(is_obs=[ObsState.SCANNING])
    def Scan_completed(self, return_code):
        """
        Method that manages device state in response to completion of
        the `Scan` command.
        """
        self._obs_state = ObsState.READY

    def is_EndScan_allowed(self):
        """
        Check if command `EndScan` is allowed in the current device state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return guard.require(self, "is_EndScan_allowed",
                             is_obs=[ObsState.SCANNING])

    @command(
    )
    @DebugIt()
    def EndScan(self):
        """
        End the scan

        :note: Subclasses that implement this functionality are
            recommended to leave this command as currently implemented,
            and instead override the stateless hook
            ``do_EndScan()``.
        """
        self._call_with_pattern()

    def EndScan_requested(self):
        """
        Method that manages device state in response to `EndScan`
        command being invoked.
        """
        pass

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

    def EndScan_completed(self, return_code):
        """
        Method that manages device state in response to completion of
        the `EndScan` command.
        """
        self._obs_state = ObsState.READY

    def is_EndSB_allowed(self):
        """
        Check if command `EndSB` is allowed in the current device state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return guard.require(self, "is_EndSB_allowed",
                             is_obs=[ObsState.READY])

    @command(
    )
    @DebugIt()
    def EndSB(self):
        # PROTECTED REGION ID(SKASubarray.EndSB) ENABLED START #
        """
        End the scan block.

        :note: Subclasses that implement this functionality are
            recommended to leave this command as currently implemented,
            and instead override the stateless hook
            ``do_EndSB()``.
        """
        self._call_with_pattern()

    def EndSB_requested(self):
        """
        Method that manages device state in response to `EndSB` command
        being invoked.
        """
        pass

    def do_EndSB(self):
        """
        Stateless hook for implementation of ``EndSB()`` command.
        Subclasses that have no need to override the default
        implementation of state management may leave ``EndSB()`` alone
        and override this method instead.

        :return: A tuple containing a return code and a string message
            indicating status. The message is for information purpose
            only.
        :rtype: (ReturnCode, str)
        """
        return (ReturnCode.OK, "EndSB successful")

    def EndSB_completed(self, return_code):
        """
        Method that manages device state in response to completion of
        the `EndSB` command.
        """
        self._obs_state = ObsState.IDLE

    def is_Abort_allowed(self):
        """
        Check if command `Abort` is allowed in the current device state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return guard.require(
            self,
            "is_Abort_allowed",
            is_obs=[ObsState.CONFIGURING, ObsState.READY, ObsState.SCANNING]
        )

    @command(
    )
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
        self._call_with_pattern()

    def Abort_requested(self):
        """
        Method that manages device state in response to `Abort` command
        being invoked.
        """
        pass

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

    def Abort_completed(self, return_code):
        """
        Method that manages device state in response to completion of
        the `Abort` command.
        """
        self._obs_state = ObsState.ABORTED

    def is_Reset_allowed(self):
        """
        Check if command `Reset` is allowed in the current device state.

        This command has a special semantics for subarrays: it is
        essentially passed through to the nested observation state
        machine, and resets that, rather than the subarray itself. That
        is: the subarray stops any ongoing observation activity,
        and deconfigures, but it does NOT release its resources or
        change device state. Thus it only makes sense for
        an enabled, online, resourced subarray.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return guard.require(
            self,
            "is_Reset_allowed",
            is_obs=[ObsState.CONFIGURING, ObsState.READY, ObsState.SCANNING,
                    ObsState.ABORTED]
        )

    @command(
    )
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
        self._call_with_pattern()

    def do_reset(self):
        """
        Stateless hook for implementation of ``Reset()`` command.
        Subclasses that have no need to override the default
        implementation of state management may leave ``EndScan()`` alone
        and override this method instead.

        :return: A tuple containing a return code and a string message
            indicating status. The message is for information purpose
            only.
        :rtype: (ReturnCode, str)
        """
        # Don't call superclass command because this command has a completely
        # different semantics for subarrays.

        # Here we need to abort any configuring or running scan
        pass

        # Now totally deconfigure
        for capability_type in self._configured_capabilities:
            self._configured_capabilities[capability_type] = 0

        return (ReturnCode.OK, "Reset successful")

    def Reset_completed(self, return_code):
        """
        Method that manages device state in response to completion of
        the `Reset` command.
        """
        self._obs_state = ObsState.IDLE

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
