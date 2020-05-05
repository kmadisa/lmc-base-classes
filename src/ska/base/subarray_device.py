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
from ska.base.control_model import AdminMode, ObsState, device_check
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

        :return: A list of capability types with no. of instances
        used in the Subarray
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

    @device_check(
        admin_modes=[AdminMode.ONLINE, AdminMode.MAINTENANCE],
        states=[DevState.OFF, DevState.ON],
        obs_states=[ObsState.IDLE]
    )
    def is_AssignResources_allowed(self):
        """
        Check if command `AssignResources` is allowed in the current
        device state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return True  # but see decorator

    @command(dtype_in=('str',), doc_in="List of Resources to add to subarray.", dtype_out=('str',),
             doc_out="A list of Resources added to the subarray.",)
    @DebugIt()
    def AssignResources(self, argin):
        # PROTECTED REGION ID(SKASubarray.AssignResources) ENABLED START #
        """Assign resources to a Subarray"""
        argout = []
        resources = self._assigned_resources[:]
        for resource in argin:
            if resource not in resources:
                self._assigned_resources.append(resource)
            argout.append(resource)

        self.set_state(DevState.ON)
        return argout

    @device_check(is_obs=[ObsState.IDLE])
    def is_ReleaseResources_allowed(self):
        """
        Check if command `ReleaseResources` is allowed in the current
        device state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return True  # but see decorator

    @command(dtype_in=('str',), doc_in="List of resources to remove from the subarray.", dtype_out=('str',),
             doc_out="List of resources removed from the subarray.",)
    @DebugIt()
    def ReleaseResources(self, argin):
        # PROTECTED REGION ID(SKASubarray.ReleaseResources) ENABLED START #
        """Delta removal of assigned resources."""
        argout = []
        # Release resources...
        resources = self._assigned_resources[:]
        for resource in argin:
            if resource in resources:
                self._assigned_resources.remove(resource)
            argout.append(resource)

        if not self._assigned_resources:
            self.set_state(DevState.OFF)

        return argout
        # PROTECTED REGION END #    //  SKASubarray.ReleaseResources

    @device_check(is_obs=[ObsState.IDLE])
    def is_ReleaseAllResources_allowed(self):
        """
        Check if command `ReleaseAllResources` is allowed in the current
        device state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return True  # but see decorator

    @command(dtype_out=('str',), doc_out="List of resources removed from the subarray.",)
    @DebugIt()
    def ReleaseAllResources(self):
        # PROTECTED REGION ID(SKASubarray.ReleaseAllResources) ENABLED START #
        """Remove all resources to tear down to an empty subarray."""
        resources = self._assigned_resources[:]
        released_resources = self.ReleaseResources(resources)

        self.set_state(DevState.OFF)
        return released_resources
        # PROTECTED REGION END #    //  SKASubarray.ReleaseAllResources

    @device_check(is_obs=[ObsState.IDLE, ObsState.READY])
    def is_ConfigureCapability_allowed(self):
        """
        Check if command `ConfigureCapability` is allowed in the current
        device state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return True  # but see decorator

    @command(dtype_in='DevVarLongStringArray', doc_in="[Number of instances to add][Capability types]",)
    @DebugIt()
    def ConfigureCapability(self, argin):
        """
        Configures the capabilities of this subarray

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
            self.configure_capability_completed()

    def do_configure_capability(self, argin):
        """
        Configures number of instances for each capability. If the capability exists,
        it increments the configured instances by the number of instances requested,
        otherwise an exception will be raised.
        Note: The two lists arguments must be of equal length or an exception will be raised.

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

    @device_check(is_obs=[ObsState.CONFIGURING])
    def configure_capability_completed(self):
        """
        Updates device state following successful configuration.
        """
        self._obs_state = ObsState.READY

    @device_check(is_obs=[ObsState.READY])
    def is_DeconfigureAllCapabilities_allowed(self):
        """
        Check if command `DeconfigureAllCapabilities` is allowed in the
        current device state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return True  # but see decorator

    @command(dtype_in='str', doc_in="Capability type",)
    @DebugIt()
    def DeconfigureAllCapabilities(self, argin):
        # PROTECTED REGION ID(SKASubarray.DeconfigureAllCapabilities) ENABLED START #i
        """Deconfigure all instances of the given Capability type. If the capability
        type does not exist an exception will be raised, otherwise it sets the
        configured instances for that capability type to zero."""
        self._validate_capability_types('DeconfigureAllCapabilities', [argin])
        self._configured_capabilities[argin] = 0

        if not any(self._configured_capabilities.values()):  # subarray is empty
            self._obs_state = ObsState.IDLE
        # PROTECTED REGION END #    //  SKASubarray.DeconfigureAllCapabilities

    @device_check(is_obs=[ObsState.READY])
    def is_DeconfigureCapability_allowed(self):
        """
        Check if command `DeconfigureCapability` is allowed in the
        current device state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return True  # but see decorator

    @command(dtype_in='DevVarLongStringArray', doc_in="[Number of instances to remove][Capability types]",)
    @DebugIt()
    def DeconfigureCapability(self, argin):
        # PROTECTED REGION ID(SKASubarray.DeconfigureCapability) ENABLED START #
        """Deconfigures a given number of instances for each capability.
        If the capability exists, it decrements the configured instances by the
        number of instances requested, otherwise an exceptioin will be raised.
        Note: The two lists arguments must be of equal length or an exception
        will be raised"""
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

        if not any(self._configured_capabilities.values()):  # subarray is empty
            self._obs_state = ObsState.IDLE
        # PROTECTED REGION END #    //  SKASubarray.DeconfigureCapability

    @device_check(is_obs=[ObsState.READY])
    def is_Scan_allowed(self):
        """
        Check if command `Scan` is allowed in the current device state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return True  # but see decorator

    @command(dtype_in=('str',),)
    @DebugIt()
    def Scan(self, argin):
        """
        Starts the scan
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
            self.scan_completed()

    def do_scan(self, argin):
        """
        Hook for the asynchronous scan code. At present this is an empty
        stub that returns False.

        :return: Whether the scan completed successfully.
        :rtype: boolean
        """
        # For this synchronous version of the code, we won't let the
        # scan complete; we'll force the device to remain in SCANNING
        # mode until we interrupt it e.g. with EndScan() or Abort().
        return False

    @device_check(is_obs=[ObsState.SCANNING])
    def scan_completed(self):
        """
        Updates device state following the successful completion of a
        scan.
        """
        self._obs_state = READY

    @device_check(is_obs=[ObsState.SCANNING])
    def is_EndScan_allowed(self):
        """
        Check if command `EndScan` is allowed in the current device state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return True  # but see decorator

    @command(
    )
    @DebugIt()
    def EndScan(self):
        # PROTECTED REGION ID(SKASubarray.EndScan) ENABLED START #
        """Ends the scan"""
        self._obs_state = ObsState.READY
        # PROTECTED REGION END #    //  SKASubarray.EndScan

    @device_check(is_obs=[ObsState.READY])
    def is_EndSB_allowed(self):
        """
        Check if command `EndSB` is allowed in the current device state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return True  # but see decorator

    @command(
    )
    @DebugIt()
    def EndSB(self):
        # PROTECTED REGION ID(SKASubarray.EndSB) ENABLED START #
        """Change obsState to IDLE."""
        self._obs_state = ObsState.IDLE
        # PROTECTED REGION END #    //  SKASubarray.EndSB

    @device_check(
        is_obs=[ObsState.CONFIGURING, ObsState.READY, ObsState.SCANNING]
    )
    def is_Abort_allowed(self):
        """
        Check if command `Abort` is allowed in the current device state.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return True  # but see decorator

    @command(
    )
    @DebugIt()
    def Abort(self):
        # PROTECTED REGION ID(SKASubarray.Abort) ENABLED START #
        """Change obsState to ABORTED."""
        self._obs_state = ObsState.ABORTED
        # PROTECTED REGION END #    //  SKASubarray.Abort

    @device_check(
        is_obs=[ObsState.CONFIGURING, ObsState.READY, ObsState.SCANNING,
                ObsState.ABORTED]
    )
    def is_Reset_allowed(self):
        """
        Check if command `Reset` is allowed in the current device state.

        This isn't implemented in parent classes, which implies that it
        may be called from any device state, which does make sense for a
        reset. For subarrays, however, Reset() is defined as: "stop what
        you're doing, deconfigure, but don't release resources." Thus
        for subarrays the Reset() command only makes sense in ON states.

        :raises ``tango.DevFailed``: if the command is not allowed
        :return: ``True`` if the command is allowed
        :rtype: boolean
        """
        return True  # but see decorator

    @command(
    )
    @DebugIt()
    def Reset(self):
        # PROTECTED REGION ID(SKASubarray.Abort) ENABLED START #
        """
        Reset the subarray.

        This command has a special and unusual semantics for subarrays:
        resetting a subarray causes it to stop what it is doing, and
        deconfigure, but NOT to release its resources. Thus is only
        makes sense for an enabled, online, resourced subarray.
        """

        if self.get_state() == DevState.ON:
            # abort any configuring or running scan

            # totally deconfigure
            for capability_type in self._configured_capabilities:
                self._configured_capabilities[capability_type] = 0

            self._obs_state = ObsState.IDLE

        # PROTECTED REGION END #    //  SKASubarray.Abort

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
