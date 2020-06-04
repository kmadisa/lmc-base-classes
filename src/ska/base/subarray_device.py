# -*- coding: utf-8 -*-
#
# This file is part of the SKASubarray project
#
#
#
""" SKASubarray

A SubArray handling device. It allows the assigning/releasing of resources into/from Subarray, configuring
capabilities, and exposes the related information like assigned resources, configured capabilities, etc.
"""
# PROTECTED REGION ID(SKASubarray.additionnal_import) ENABLED START #
# Standard imports
import os
import sys

# Tango imports
from tango import DebugIt
from tango import AttrWriteType, DevState, Except, ErrSeverity
from tango.server import run, attribute, command
from tango.server import device_property

# SKA specific imports
from ska.base import SKAObsDevice, release
from ska.base.control_model import AdminMode, ObsState, guard
# PROTECTED REGION END #    //  SKASubarray.additionnal_imports

__all__ = ["SKASubarray", "main"]


class SKASubarray(SKAObsDevice):
    """
    SubArray handling device
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


    # PROTECTED REGION END #    //  SKASubarray.class_variable

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

    def do_init_device(self):
        """
        Method that initialises device attribute and other internal
        values. Subclasses that have no need to override the default
        implementation of state management and asynchrony may leave
        ``init_device`` alone and override this method instead.
        """
        super().do_init_device()

        self._build_state = '{}, {}, {}'.format(release.name, release.version,
                                                release.description)
        self._version_id = release.version

        # Subarrays are logical devices, and a pool of them is created
        # at start-up, to be put online and used as needed, Therefore
        # the subarray adminMode is initialised into adminMode OFFLINE,
        # and is NOT memorized.
        self._admin_mode = AdminMode.OFFLINE

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
        return guard.require(self, "is_AssignResources_allowed",
            admin_modes=[AdminMode.ONLINE, AdminMode.MAINTENANCE],
            states=[DevState.OFF, DevState.ON],
            obs_states=[ObsState.IDLE]
        )

    @command(dtype_in=('str',), doc_in="List of Resources to add to subarray.", dtype_out=('str',),
             doc_out="A list of Resources added to the subarray.",)
    @DebugIt()
    def AssignResources(self, argin):
        # PROTECTED REGION ID(SKASubarray.AssignResources) ENABLED START #
        """
        Assign resources to a subarray.

        :note: Subclasses that augment assign_resources functionality
            may either override ``AssignResources()``, in which case
            they must manage state, or override
            ``do_assign_resources()`` in which case this class will
            continue to manage state in accordance with the subarray
            control model.
        :return: list of resources added
        :rtype: list of string
        """
        assigned = self.do_assign_resources(argin)
        self.set_state(DevState.ON)
        return assigned

    def do_assign_resources(self, argin):
        """
        Perform actions necessary to assign resources.

        :note: Subclasses that augment assign_resources functionality
            may either override ``AssignResources()``, in which case
            they must manage state, or override
            ``do_assign_resources()`` in which case this class will
            continue to manage state in accordance with the subarray
            control model.
        :return: list of resources added
        :rtype: list of string
        """
        argout = []
        resources = self._assigned_resources[:]
        for resource in argin:
            if resource not in resources:
                self._assigned_resources.append(resource)
            argout.append(resource)
        return argout

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
        doc_in="List of resources to remove from the subarray.", dtype_out=('str',),
        doc_out="List of resources removed from the subarray.",
    )
    @DebugIt()
    def ReleaseResources(self, argin):
        """
        Delta removal of assigned resources.

        :note: Subclasses that augment release_resources functionality
            may either override ``ReleaseResources()``, in which case
            they must manage state, or override
            ``do_release_resources()`` in which case this class will
            continue to manage state in accordance with the subarray
            control model.
        :return: list of resources removed
        :rtype: list of string
        """
        released_resources = self.do_release_resources(argin)

        if not self._assigned_resources:
            self.set_state(DevState.OFF)

        return released_resources

    def do_release_resources(self, argin):
        """
        Perform actions necessary to release resources.

        :note: Subclasses that augment release_resources functionality
            may either override ``ReleaseResources()``, in which case
            they must manage state, or override
            ``do_release_resources()`` in which case this class will
            continue to manage state in accordance with the subarray
            control model.
        :return: list of resources removed
        :rtype: list of string
        """
        argout = []
        # Release resources...
        resources = self._assigned_resources[:]
        for resource in argin:
            if resource in resources:
                self._assigned_resources.remove(resource)
            argout.append(resource)

        return argout
        # PROTECTED REGION END #    //  SKASubarray.ReleaseResources

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

    @command(dtype_out=('str',), doc_out="List of resources removed from the subarray.",)
    @DebugIt()
    def ReleaseAllResources(self):
        # PROTECTED REGION ID(SKASubarray.ReleaseAllResources) ENABLED START #
        """
        Remove all resources to tear down to an empty subarray.

        :note: Subclasses that augment release_all_resources
            functionality may either override ``ReleaseAllResources()``,
            in which case they must manage state, or override
            ``do_release_all_resources()`` in which case this class will
            continue to manage state in accordance with the subarray
            control model.
        :return: list of resources removed
        :rtype: list of string
        """

        released_resources = self.do_release_all_resources()
        self.set_state(DevState.OFF)
        return released_resources
        # PROTECTED REGION END #    //  SKASubarray.ReleaseAllResources

    def do_release_all_resources(self):
        """
        Perform actions necessary to release all resources.

        :note: Subclasses that augment release_all_resources
            functionality may either override ``ReleaseAllResources()``,
            in which case they must manage state, or override
            ``do_release_all_resources()`` in which case this class will
            continue to manage state in accordance with the subarray
            control model.
        :return: list of resources removed
        :rtype: list of string
        """
        resources = self._assigned_resources[:]
        return self.do_release_resources(resources)

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

    @command(dtype_in='DevVarLongStringArray', doc_in="[Number of instances to add][Capability types]",)
    @DebugIt()
    def ConfigureCapability(self, argin):
        """
        Configures the capabilities of this subarray

        :note: Subclasses that augment configure_capability
            functionality may either override ``ConfigureCapability()``,
            in which case they must manage state, or override
            ``do_configure_capability()`` in which case this class will
            continue to manage state in accordance with the subarray
            control model.
        :param argin: configuration specification
        :type argin: string
        """
        self._obs_state = ObsState.CONFIGURING
        self.run_configure_capability(argin)

    def run_configure_capability(self, argin):
        """
        Performs and monitors the configuring. Then, if the configuring
        completed successfully, updates the obsState from CONFIGURING to
        READY. If the configuring does not complete successfully, the
        state is not updated, because it is assumed that this will be
        handled by whatever has interrupted it e.g. an Abort().

        This functionality is enclosed in its own method as a hook for
        future implementation of asynchrony.

        :param argin: configuration specification
        :type argin: string
        """
        if self.do_configure_capability(argin):
            self.post_configure_capability()

    def do_configure_capability(self, argin):
        """
        Configures number of instances for each capability. If the
        capability exists, it increments the configured instances by the
        number of instances requested, otherwise an exception will be
        raised. Note: The two list arguments must be of equal length or
        an exception will be raised.

        :note: Subclasses that augment configure_capability
            functionality may either override ``ConfigureCapability()``,
            in which case they must manage state, or override
            ``do_configure_capability()`` in which case this class will
            continue to manage state in accordance with the subarray
            control model.
        :return: whether the configuration completed successfully
        :rtype: boolean
        """
        command_name = 'ConfigureCapability'

        capabilities_instances, capability_types = argin
        self._validate_capability_types(command_name, capability_types)
        self._validate_input_sizes(command_name, argin)

        # Perform the configuration.
        for capability_instances, capability_type in zip(
                capabilities_instances, capability_types):
            self._configured_capabilities[capability_type] += capability_instances

        return True

    @guard(is_obs=[ObsState.CONFIGURING])
    def post_configure_capability(self):
        """
        Updates device state following successful configuration.
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

        :note: Subclasses that augment deconfigure_all_capabilities
            functionality may either override
            ``DeconfigureAllCapabilities()``, in which case they must
            manage state, or override
            ``do_deconfigure_all_capabilities()`` in which case this
            class will continue to manage state in accordance with the
            subarray control model.
        """
        self._obs_state = ObsState.CONFIGURING
        self.do_deconfigure_all_capabilities(argin)

        if self.is_configured():
            self._obs_state = ObsState.READY
        else:
            self._obs_state = ObsState.IDLE

    def do_deconfigure_all_capabilities(self, argin):
        """
        Perform actions necessary to deconfigure all capabilities of the
        given capability type.

        If the capability type does not exist, an exception will be
        raised. Otherwise it sets the configured instances for that
        capability type to zero.

        :note: Subclasses that augment deconfigure_all_capabilities
            functionality may either override
            ``DeconfigureAllCapabilities()``, in which case they must
            manage state, or override
            ``do_deconfigure_all_capabilities()`` in which case this
            class will continue to manage state in accordance with the
            subarray control model.
        """
        self._validate_capability_types('DeconfigureAllCapabilities', [argin])
        self._configured_capabilities[argin] = 0

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

    @command(dtype_in='DevVarLongStringArray', doc_in="[Number of instances to remove][Capability types]",)
    @DebugIt()
    def DeconfigureCapability(self, argin):
        """
        Deconfigures a given number of instances for each capability.

        :note: Subclasses that augment deconfigure capability
            functionality may either override
            ``DeconfigureCapability()``, in which case they must manage
            state, or override ``do_deconfigure_capability()`` (and if
            necessary ``is_configured()``), in which case this class
            will continue to manage state in accordance with the
            subarray control model.
        """
        self._obs_state = ObsState.CONFIGURING
        self.do_deconfigure_capability(argin)

        if self.is_configured():
            self._obs_state = ObsState.READY
        else:
            self._obs_state = ObsState.IDLE

    def do_deconfigure_capability(self, argin):
        """
        Perform actions necessary to deconfigure a capability.

        If the capability exists, it decrements the configured instances
        by the number of instances requested, otherwise an exception
        will be raised. Note: The two list arguments must be of equal
        length or an exception will be raised.

        :note: Subclasses that augment deconfigure capability
            functionality may either override
            ``DeconfigureCapability()``, in which case they must manage
            state, or override ``do_deconfigure_capability()`` (and if
            necessary ``is_configured()``), in which case this class
            will continue to manage state in accordance with the
            subarray control model.
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

        :note: Subclasses that augment scan functionality may either
            override ``Scan()``, in which case they must manage state
            and (eventually) asynchrony, or override ``do_scan()`` in
            which case this class will continue to manage state and
            asynchrony in accordance with the subarray control model.
        """
        self._obs_state = ObsState.SCANNING
        self.run_scan(argin)

    def run_scan(self, argin):
        """
        Performs and monitors the scan. Then, if the scan completed
        successfully, updates the obsState from SCANNING to READY. If
        the scan does not complete successfully, the state is not
        updated, because it is assumed that this will be handled by
        whatever has interrupted the scan e.g. an Abort() or EndScan()
        call.

        This functionality is enclosed in its own method as a hook for
        future implementation of asynchrony.

        :param argin: scan arg
        :type argin: string
        """
        if self.do_scan(argin):
            self.post_scan()

    def do_scan(self, argin):
        """
        Perform actions necessary to start a scan.

        At present this is an empty stub that returns False.

        :note: Subclasses that augment scan functionality may either
            override ``Scan()``, in which case they must manage state
            and (eventually) asynchrony, or override ``do_scan()`` in
            which case this class will continue to manage state and
            asynchrony in accordance with the subarray control model.

        :return: Whether the scan completed successfully.
        :rtype: boolean
        """
        # For this synchronous version of the code, we won't let the
        # scan complete; we'll force the device to remain in SCANNING
        # mode until we interrupt it e.g. with EndScan() or Abort().
        return False

    @guard(is_obs=[ObsState.SCANNING])
    def post_scan(self):
        """
        Updates device state following the successful completion of a
        scan.
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
        # PROTECTED REGION ID(SKASubarray.EndScan) ENABLED START #
        """
        End the scan

        :note: Subclasses that augment endscan functionality may either
            override ``EndScan()``, in which case they must manage
            state, or override ``do_end_scan()`` in which case this
            class will continue to manage state in accordance with the
            subarray control model.
        """
        if self.do_end_scan():
            self._obs_state = ObsState.READY
        # PROTECTED REGION END #    //  SKASubarray.EndScan

    def do_end_scan(self):
        """
        Perform actions necessary to end a scan.

        :note: Subclasses that augment endscan functionality may either
            override ``EndScan()``, in which case they must manage
            state, or override ``do_end_scan()`` in which case this
            class will continue to manage state in accordance with the
            subarray control model.
        :return: whether the actions were performed successfully
        :rtype: boolean
        """
        return True

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

        :note: Subclasses that augment endSB functionality may either
            override ``EndSB()``, in which case they must manage state,
            or override ``do_end_SB()`` in which case this class will
            continue to manage state in accordance with the subarray
            control model.
        """
        if self.do_end_SB():
            self._obs_state = ObsState.IDLE
        # PROTECTED REGION END #    //  SKASubarray.EndSB

    def do_end_SB(self):
        """
        Perform actions necessary to end a scanblock.

        :note: Subclasses that augment endSB functionality may either
            override ``EndSB()``, in which case they must manage state,
            or override ``do_end_SB()`` in which case this class will
            continue to manage state in accordance with the subarray
            control model.
        :return: whether the actions were performed successfully
        :rtype: boolean
        """
        return True

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
        # PROTECTED REGION ID(SKASubarray.Abort) ENABLED START #
        """
        Abort any long-running command such as ``Configure()`` or
        ``Scan()``.

        :note: Subclasses that augment abort functionality may either
            override ``Abort()``, in which case they must manage state,
            or override ``do_abort()`` in which case this class will
            continue to manage state in accordance with the subarray
            control model.
        """
        if self.do_abort():
            self._obs_state = ObsState.ABORTED
        # PROTECTED REGION END #    //  SKASubarray.Abort

    def do_abort(self):
        """
        Perform actions as part of an abort.

        :note: Subclasses that augment abort functionality may either
            override ``Abort()``, in which case they must manage state,
            or override ``do_abort()`` in which case this class will
            continue to manage state in accordance with the subarray
            control model.
        :return: whether the actions were performed successfully
        :rtype: boolean
        """
        # Here we should stop any current running configuring or scan.
        return True

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

        :note: Subclasses that augment reset functionality may either
            override ``Reset()``, in which case they must manage state,
            or override ``do_reset()`` in which case this class will
            continue to manage state in accordance with the subarray
            control model.
        """
        if self.do_reset():
            self._obs_state = ObsState.IDLE

    def do_reset(self):
        """
        Perform actions necessary for a reset.

        :note: Subclasses that augment reset functionality may either
            override ``Reset()``, in which case they must manage state,
            or override ``do_reset()`` in which case this class will
            continue to manage state in accordance with the subarray
            control model.
        :return: whether the actions were performed successfully
        :rtype: boolean
        """
        # Here we need to abort any configuring or running scan
        pass

        # Now totally deconfigure
        for capability_type in self._configured_capabilities:
            self._configured_capabilities[capability_type] = 0

        return True

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
