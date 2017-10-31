# -*- coding: utf-8 -*-
#
# This file is part of the SKASubarray project
#
#
#
# Distributed under the terms of the GPL license.
# See LICENSE.txt for more info.

""" SKASubarray

SubArray handling device
"""

# PyTango imports
import PyTango
from PyTango import DebugIt
from PyTango.server import run
from PyTango.server import Device, DeviceMeta
from PyTango.server import attribute, command
from PyTango.server import device_property
from PyTango import AttrQuality, DispLevel, DevState
from PyTango import AttrWriteType, PipeWriteType
from SKAObsDevice import SKAObsDevice
# Additional import
# PROTECTED REGION ID(SKASubarray.additionnal_import) ENABLED START #
from PyTango import DeviceProxy, Except, ErrSeverity
# PROTECTED REGION END #    //  SKASubarray.additionnal_import

__all__ = ["SKASubarray", "main"]


class SKASubarray(SKAObsDevice):
    """
    SubArray handling device
    """
    __metaclass__ = DeviceMeta
    # PROTECTED REGION ID(SKASubarray.class_variable) ENABLED START #
    def __init__(self, *args, **kwargs):
        super(SKASubarray, self).__init__(*args, **kwargs)

        # Initialize attribute values.
        self._activation_time = 0.0
        self._max_capabilities = [0]
        self._available_capabilites = [0]
        self._assigned_resources = [""]
        self._configured_capabilites = [""]
    # PROTECTED REGION END #    //  SKASubarray.class_variable

    # -----------------
    # Device Properties
    # -----------------







    SubID = device_property(
        dtype='str',
    )

    CapabililtyTypes = device_property(
        dtype=('str',),
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















    maxCapabilities = attribute(
        dtype=('uint16',),
        max_dim_x=10,
        doc="Maximum instances of each capability type, in the same order as the CapabilityTypes",
    )

    availableCapabilities = attribute(
        dtype=('uint16',),
        max_dim_x=10,
        doc="Available instances of each capability type, in the same order as the CapabilityTypes",
    )

    assignedResources = attribute(
        dtype=('str',),
        max_dim_x=100,
        doc="The list of resources assigned to the subarray.",
    )

    configuredCapabilities = attribute(
        dtype=('str',),
        max_dim_x=10,
        doc="A list of capability types with no. of instances in use on this subarray; e.g.\nCorrelators:512, PssBeams:4, PstBeams:4, VlbiBeams:0.",
    )

    # ---------------
    # General methods
    # ---------------

    def init_device(self):
        SKAObsDevice.init_device(self)
        # PROTECTED REGION ID(SKASubarray.init_device) ENABLED START #

        # When Subarray in not in use it reports:
        self.set_state(DevState.DISABLE)

        # PROTECTED REGION END #    //  SKASubarray.init_device

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
        return self._activation_time
        # PROTECTED REGION END #    //  SKASubarray.activationTime_read

    def read_maxCapabilities(self):
        # PROTECTED REGION ID(SKASubarray.maxCapabilities_read) ENABLED START #
        return self._max_capabilities
        # PROTECTED REGION END #    //  SKASubarray.maxCapabilities_read

    def read_availableCapabilities(self):
        # PROTECTED REGION ID(SKASubarray.availableCapabilities_read) ENABLED START #
        self._available_capabilites
        # PROTECTED REGION END #    //  SKASubarray.availableCapabilities_read

    def read_assignedResources(self):
        # PROTECTED REGION ID(SKASubarray.assignedResources_read) ENABLED START #
        return self._assigned_resources
        # PROTECTED REGION END #    //  SKASubarray.assignedResources_read

    def read_configuredCapabilities(self):
        # PROTECTED REGION ID(SKASubarray.configuredCapabilities_read) ENABLED START #
        return self._configured_capabilities
        # PROTECTED REGION END #    //  SKASubarray.configuredCapabilities_read


    # --------
    # Commands
    # --------

    @command(
    dtype_in=('str',),
    doc_in="List of Resources to add to subarray.",
    dtype_out=('str',),
    doc_out="A list of Resources added to the subarray.",
    )
    @DebugIt()
    def AssignResources(self, argin):
        # PROTECTED REGION ID(SKASubarray.AssignResources) ENABLED START #
        # There currently is no way of get an attributes enum labels using the Device
        # object. So I am going to use the DeviceProxy for now.
        dp = DeviceProxy(self.get_name())

        obstate_labels = list(dp.attribute_query('obsState').enum_labels)
        obs_idle = obstate_labels.index('IDLE')

        admin_labels = list(dp.attribute_query('adminMode').enum_labels)
        admin_online = admin_labels.index('ON-LINE')
        admin_maintenance = admin_labels.index('MAINTENANCE')
        admin_offline = admin_labels.index('OFF-LINE')
        admin_not_fitted = admin_labels.index('NOT-FITTED')

        argout = []

        if (self.read_adminMode() == admin_offline or
                self.read_adminMode() == admin_not_fitted):
            # Raise an error...
            Except.throw_exception("Command failed!",  "Subarray adminMode is 'OFF-LINE'"
                                   " or in 'NOT-FITTED'", "ReleaseResources",
                                   ErrSeverity.ERR)

        if self.read_obsState() == obs_idle:
            if (self.read_adminMode() == admin_online or
                    self.read_adminMode() == admin_maintenance):
                # Assign resources...
                resources = self._assigned_resources[:]
                for resource in argin:
                    if resource not in resources:
                        self._assigned_resources.append(resource)
                    argout.append(resource)
            else:
                Except.throw_exception("Command failed!", "Subarray adminMode not"
                                       " 'ON-LINE' or in 'MAINTENANCE'.",
                                       "ReleaseResources", ErrSeverity.ERR)

        else:
            # Raise an error...
            Except.throw_exception("Command failed!",  "Subarray obsState not 'IDLE'.",
                                   "ReleaseResources", ErrSeverity.ERR)
        return argout

    @command(
    dtype_in=('str',),
    doc_in="List of resources to remove from the subarray.",
    dtype_out=('str',),
    doc_out="List of resources removed from the subarray.",
    )
    @DebugIt()
    def ReleaseResources(self, argin):
        # PROTECTED REGION ID(SKASubarray.ReleaseResources) ENABLED START #
        dp = DeviceProxy(self.get_name())

        obstate_labels = list(dp.attribute_query('obsState').enum_labels)
        obs_idle = obstate_labels.index('IDLE')

        admin_labels = list(dp.attribute_query('adminMode').enum_labels)
        admin_online = admin_labels.index('ON-LINE')
        admin_maintenance = admin_labels.index('MAINTENANCE')
        admin_offline = admin_labels.index('OFF-LINE')
        admin_not_fitted = admin_labels.index('NOT-FITTED')

        argout = []

        if (self.read_adminMode() == admin_offline or
                self.read_adminMode() == admin_not_fitted):
            # Raise an error...
            Except.throw_exception("Command failed!", "Subarray adminMode is 'OFF-LINE'"
                                   " or in 'NOT-FITTED'.", "ReleaseResources",
                                   ErrSeverity.ERR)

        if self.read_obsState() == obs_idle:
            if (self.read_adminMode() == admin_online or
                    self.read_adminMode() == admin_maintenance):
                # Release resources...
                resources = self._assigned_resources[:]
                for resource in argin:
                    if resource in resources:
                        self._assigned_resources.remove(resource)
                        argout.append(resource)
            else:
                Except.throw_exception("Command failed!", "Subarray adminMode not"
                                       " 'ON-LINE' or in 'MAINTENANCE'.",
                                       "ReleaseResources", ErrSeverity.ERR)

        else:
            # Raise an error...
            Except.throw_exception("Command failed!",  "Subarray obsState not 'IDLE'.",
                                   "ReleaseResources", ErrSeverity.ERR)
        return argout
        # PROTECTED REGION END #    //  SKASubarray.ReleaseResources

    @command(
    dtype_out=('str',),
    doc_out="List of resources removed from the subarray.",
    )
    @DebugIt()
    def ReleaseAllResources(self):
        # PROTECTED REGION ID(SKASubarray.ReleaseAllResources) ENABLED START #
        resources = self._assigned_resources[:]
        released_resources = self.ReleaseResources(resources)
        #if self._assigned_resources == []:
        #    self.set_state(DevState.ON)
        #    admin_labels = list(dp.attribute_query('adminMode').enum_labels)
        #    admin_online = admin_labels.index('ON-LINE')
        #    self.write_adminMode(admin_online)
        #    obstate_labels = list(dp.attribute_query('obsState').enum_labels)
        #    obs_idle = obstate_labels.index('IDLE')
        #    self._obs_mode = obs_idle
        return released_resources
        # PROTECTED REGION END #    //  SKASubarray.ReleaseAllResources

    @command(
    dtype_in=('str',),
    doc_in="Capability type, nrInstances.",
    )
    @DebugIt()
    def ConfigureCapability(self, argin):
        # PROTECTED REGION ID(SKASubarray.ConfigureCapability) ENABLED START #
        pass
        # PROTECTED REGION END #    //  SKASubarray.ConfigureCapability

    @command(
    dtype_in=('str',),
    doc_in="Capability type, nrInstances",
    dtype_out='bool',
    )
    @DebugIt()
    def isCapabilityAchievable(self, argin):
        # PROTECTED REGION ID(SKASubarray.isCapabilityAchievable) ENABLED START #
        return False
        # PROTECTED REGION END #    //  SKASubarray.isCapabilityAchievable

    @command(
    )
    @DebugIt()
    def Abort(self):
        # PROTECTED REGION ID(SKASubarray.Abort) ENABLED START #
        pass
        # PROTECTED REGION END #    //  SKASubarray.Abort

    @command(
    )
    @DebugIt()
    def EndSB(self):
        # PROTECTED REGION ID(SKASubarray.EndSB) ENABLED START #
        pass
        # PROTECTED REGION END #    //  SKASubarray.EndSB

    @command(
    dtype_in=('str',),
    )
    @DebugIt()
    def Scan(self, argin):
        # PROTECTED REGION ID(SKASubarray.Scan) ENABLED START #
        pass
        # PROTECTED REGION END #    //  SKASubarray.Scan

    @command(
    )
    @DebugIt()
    def EndScan(self):
        # PROTECTED REGION ID(SKASubarray.EndScan) ENABLED START #
        pass
        # PROTECTED REGION END #    //  SKASubarray.EndScan

    @command(
    )
    @DebugIt()
    def Pause(self):
        # PROTECTED REGION ID(SKASubarray.Pause) ENABLED START #
        pass
        # PROTECTED REGION END #    //  SKASubarray.Pause

    @command(
    )
    @DebugIt()
    def Resume(self):
        # PROTECTED REGION ID(SKASubarray.Resume) ENABLED START #
        pass
        # PROTECTED REGION END #    //  SKASubarray.Resume

# ----------
# Run server
# ----------


def main(args=None, **kwargs):
    # PROTECTED REGION ID(SKASubarray.main) ENABLED START #
    return run((SKASubarray,), args=args, **kwargs)
    # PROTECTED REGION END #    //  SKASubarray.main

if __name__ == '__main__':
    main()
