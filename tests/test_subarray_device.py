#########################################################################################
# -*- coding: utf-8 -*-
#
# This file is part of the SKASubarray project
#
#
#
#########################################################################################
"""Contain the tests for the SKASubarray."""

# Standard imports
import itertools
import sys
import os

# Imports
import re
import pytest
from tango import DevState, DevSource, DevFailed

# PROTECTED REGION ID(SKASubarray.test_additional_imports) ENABLED START #
from ska.base.control_model import (
    AdminMode, ControlMode, HealthState, ObsMode, ObsState, SimulationMode, TestMode
)
# PROTECTED REGION END #    //  SKASubarray.test_additional_imports
# Device test case
# PROTECTED REGION ID(SKASubarray.test_SKASubarray_decorators) ENABLED START #
@pytest.mark.usefixtures("tango_context", "initialize_device")
# PROTECTED REGION END #    //  SKASubarray.test_SKASubarray_decorators
class TestSKASubarray(object):
    """Test case for packet generation."""

    properties = {
        'CapabilityTypes': '',
        'GroupDefinitions': '',
        'SkaLevel': '4',
        'LoggingTargetsDefault': '',
        'SubID': '',
        }

    @classmethod
    def mocking(cls):
        """Mock external libraries."""
        # Example : Mock numpy
        # cls.numpy = SKASubarray.numpy = MagicMock()
        # PROTECTED REGION ID(SKASubarray.test_mocking) ENABLED START #
        # PROTECTED REGION END #    //  SKASubarray.test_mocking

    def test_properties(self, tango_context):
        # Test the properties
        # PROTECTED REGION ID(SKASubarray.test_properties) ENABLED START #
        # PROTECTED REGION END #    //  SKASubarray.test_properties
        pass

    # PROTECTED REGION ID(SKASubarray.test_Abort_decorators) ENABLED START #
    # PROTECTED REGION END #    //  SKASubarray.test_Abort_decorators
    def test_Abort(self, tango_context):
        """Test for Abort"""
        # PROTECTED REGION ID(SKASubarray.test_Abort) ENABLED START #
        tango_context.device.adminMode = AdminMode.ONLINE
        tango_context.device.AssignResources(["BAND1"])
        tango_context.device.ConfigureCapability([[2], ["BAND1"]])
        assert tango_context.device.Abort() is None
        # PROTECTED REGION END #    //  SKASubarray.test_Abort

    # PROTECTED REGION ID(SKASubarray.test_ConfigureCapability_decorators) ENABLED START #
    # PROTECTED REGION END #    //  SKASubarray.test_ConfigureCapability_decorators
    def test_ConfigureCapability(self, tango_context):
        """Test for ConfigureCapability"""
        # PROTECTED REGION ID(SKASubarray.test_ConfigureCapability) ENABLED START #
        tango_context.device.adminMode = AdminMode.ONLINE
        tango_context.device.AssignResources(["BAND1"])
        tango_context.device.ConfigureCapability([[2], ["BAND1"]])
        # The obsState attribute is changed by ConfigureCapability, but
        # as it is a polled attribute the value in the cache may be stale,
        # so change source to ensure we read directly from the device
        tango_context.device.set_source(DevSource.DEV)
        assert tango_context.device.obsState == ObsState.READY
        assert tango_context.device.configuredCapabilities == ("BAND1:2", "BAND2:0")
        # PROTECTED REGION END #    //  SKASubarray.test_ConfigureCapability

    # PROTECTED REGION ID(SKASubarray.test_DeconfigureAllCapabilities_decorators) ENABLED START #
    # PROTECTED REGION END #    //  SKASubarray.test_DeconfigureAllCapabilities_decorators
    def test_DeconfigureAllCapabilities(self, tango_context):
        """Test for DeconfigureAllCapabilities"""
        # PROTECTED REGION ID(SKASubarray.test_DeconfigureAllCapabilities) ENABLED START #
        tango_context.device.adminMode = AdminMode.ONLINE
        tango_context.device.AssignResources(["BAND1"])
        tango_context.device.ConfigureCapability([[3], ["BAND1"]])
        tango_context.device.DeconfigureAllCapabilities("BAND1")
        assert tango_context.device.configuredCapabilities == ("BAND1:0", "BAND2:0")
        # PROTECTED REGION END #    //  SKASubarray.test_DeconfigureAllCapabilities

    # TODO: Fix the test case.
    # PROTECTED REGION ID(SKASubarray.test_DeconfigureCapability_decorators) ENABLED START #
    # PROTECTED REGION END #    //  SKASubarray.test_DeconfigureCapability_decorators
    def test_DeconfigureCapability(self, tango_context):
        """Test for DeconfigureCapability"""
        # PROTECTED REGION ID(SKASubarray.test_DeconfigureCapability) ENABLED START #
        tango_context.device.adminMode = AdminMode.ONLINE
        tango_context.device.AssignResources(["BAND1"])
        tango_context.device.ConfigureCapability([[1], ["BAND1"]])
        tango_context.device.DeconfigureCapability([[1], ["BAND1"]])
        assert tango_context.device.configuredCapabilities == ("BAND1:0", "BAND2:0")
        # PROTECTED REGION END #    //  SKASubarray.test_DeconfigureCapability

    # PROTECTED REGION ID(SKASubarray.test_GetVersionInfo_decorators) ENABLED START #
    # PROTECTED REGION END #    //  SKASubarray.test_GetVersionInfo_decorators
    def test_GetVersionInfo(self, tango_context):
        """Test for GetVersionInfo"""
        # PROTECTED REGION ID(SKASubarray.test_GetVersionInfo) ENABLED START #
        versionPattern = re.compile(
            r'SKASubarray, lmcbaseclasses, [0-9].[0-9].[0-9], '
            r'A set of generic base devices for SKA Telescope.')
        versionInfo = tango_context.device.GetVersionInfo()
        assert (re.match(versionPattern, versionInfo[0])) is not None
        # PROTECTED REGION END #    //  SKASubarray.test_GetVersionInfo

    # PROTECTED REGION ID(SKASubarray.test_Status_decorators) ENABLED START #
    # PROTECTED REGION END #    //  SKASubarray.test_Status_decorators
    def test_Status(self, tango_context):
        """Test for Status"""
        # PROTECTED REGION ID(SKASubarray.test_Status) ENABLED START #
        assert tango_context.device.Status() == "The device is in DISABLE state."
        # PROTECTED REGION END #    //  SKASubarray.test_Status

    # PROTECTED REGION ID(SKASubarray.test_State_decorators) ENABLED START #
    # PROTECTED REGION END #    //  SKASubarray.test_State_decorators
    def test_State(self, tango_context):
        """Test for State"""
        # PROTECTED REGION ID(SKASubarray.test_State) ENABLED START #
        assert tango_context.device.State() == DevState.DISABLE
        # PROTECTED REGION END #    //  SKASubarray.test_State

    # PROTECTED REGION ID(SKASubarray.test_AssignResources_decorators) ENABLED START #
    # PROTECTED REGION END #    //  SKASubarray.test_AssignResources_decorators
    def test_AssignResources(self, tango_context):
        """Test for AssignResources"""
        # PROTECTED REGION ID(SKASubarray.test_AssignResources) ENABLED START #
        tango_context.device.adminMode = AdminMode.ONLINE
        tango_context.device.AssignResources(['BAND1', 'BAND2'])
        assert tango_context.device.State() == DevState.ON and \
               tango_context.device.assignedResources == ('BAND1', 'BAND2')
        tango_context.device.ReleaseAllResources()
        # PROTECTED REGION END #    //  SKASubarray.test_AssignResources

    # PROTECTED REGION ID(SKASubarray.test_EndSB_decorators) ENABLED START #
    # PROTECTED REGION END #    //  SKASubarray.test_EndSB_decorators
    def test_EndSB(self, tango_context):
        """Test for EndSB"""
        # PROTECTED REGION ID(SKASubarray.test_EndSB) ENABLED START #
        tango_context.device.adminMode = AdminMode.ONLINE
        tango_context.device.AssignResources(["BAND1"])
        tango_context.device.ConfigureCapability([[2], ["BAND1"]])
        assert tango_context.device.EndSB() is None
        # PROTECTED REGION END #    //  SKASubarray.test_EndSB

    # PROTECTED REGION ID(SKASubarray.test_EndScan_decorators) ENABLED START #
    # PROTECTED REGION END #    //  SKASubarray.test_EndScan_decorators
    def test_EndScan(self, tango_context):
        """Test for EndScan"""
        # PROTECTED REGION ID(SKASubarray.test_EndScan) ENABLED START #
        tango_context.device.adminMode = AdminMode.ONLINE
        tango_context.device.AssignResources(["BAND1"])
        tango_context.device.ConfigureCapability([[2], ["BAND1"]])
        tango_context.device.Scan([""])
        assert tango_context.device.EndScan() is None
        # PROTECTED REGION END #    //  SKASubarray.test_EndScan

    # PROTECTED REGION ID(SKASubarray.test_ReleaseAllResources_decorators) ENABLED START #
    # PROTECTED REGION END #    //  SKASubarray.test_ReleaseAllResources_decorators
    def test_ReleaseAllResources(self, tango_context):
        """Test for ReleaseAllResources"""
        # PROTECTED REGION ID(SKASubarray.test_ReleaseAllResources) ENABLED START #
        # assert tango_context.device.ReleaseAllResources() == [""]
        tango_context.device.adminMode = AdminMode.ONLINE
        tango_context.device.AssignResources(['BAND1', 'BAND2'])
        tango_context.device.ReleaseAllResources()
        assert tango_context.device.assignedResources is None
        # PROTECTED REGION END #    //  SKASubarray.test_ReleaseAllResources

    # PROTECTED REGION ID(SKASubarray.test_ReleaseResources_decorators) ENABLED START #
    # PROTECTED REGION END #    //  SKASubarray.test_ReleaseResources_decorators
    def test_ReleaseResources(self, tango_context):
        """Test for ReleaseResources"""
        # PROTECTED REGION ID(SKASubarray.test_ReleaseResources) ENABLED START #
        # assert tango_context.device.ReleaseResources([""]) == [""]
        tango_context.device.adminMode = AdminMode.ONLINE
        tango_context.device.AssignResources(['BAND1', 'BAND2'])
        tango_context.device.ReleaseResources(['BAND1'])
        assert tango_context.device.State() == DevState.ON and\
               tango_context.device.assignedResources == ('BAND2',)
        tango_context.device.ReleaseAllResources()
        # PROTECTED REGION END #    //  SKASubarray.test_ReleaseResources

    # PROTECTED REGION ID(SKASubarray.test_Reset_decorators) ENABLED START #
    # PROTECTED REGION END #    //  SKASubarray.test_Reset_decorators
    def test_Reset(self, tango_context):
        """Test for Reset"""
        # PROTECTED REGION ID(SKASubarray.test_Reset) ENABLED START #
        tango_context.device.adminMode = AdminMode.ONLINE
        tango_context.device.AssignResources(["BAND1"])
        tango_context.device.ConfigureCapability([[2], ["BAND1"]])
        assert tango_context.device.Reset() is None
        # PROTECTED REGION END #    //  SKASubarray.test_Reset

    # PROTECTED REGION ID(SKASubarray.test_Scan_decorators) ENABLED START #
    # PROTECTED REGION END #    //  SKASubarray.test_Scan_decorators
    def test_Scan(self, tango_context):
        """Test for Scan"""
        # PROTECTED REGION ID(SKASubarray.test_Scan) ENABLED START #
        tango_context.device.adminMode = AdminMode.ONLINE
        tango_context.device.AssignResources(["BAND1"])
        tango_context.device.ConfigureCapability([[2], ["BAND1"]])
        assert tango_context.device.Scan([""]) is None
        # PROTECTED REGION END #    //  SKASubarray.test_Scan

    # PROTECTED REGION ID(SKASubarray.test_activationTime_decorators) ENABLED START #
    # PROTECTED REGION END #    //  SKASubarray.test_activationTime_decorators
    def test_activationTime(self, tango_context):
        """Test for activationTime"""
        # PROTECTED REGION ID(SKASubarray.test_activationTime) ENABLED START #
        assert tango_context.device.activationTime == 0.0
        # PROTECTED REGION END #    //  SKASubarray.test_activationTime

    # PROTECTED REGION ID(SKASubarray.test_adminMode_decorators) ENABLED START #
    # PROTECTED REGION END #    //  SKASubarray.test_adminMode_decorators
    def test_adminMode(self, tango_context):
        """Test for adminMode"""
        # PROTECTED REGION ID(SKASubarray.test_adminMode) ENABLED START #
        assert tango_context.device.adminMode == AdminMode.OFFLINE
        # PROTECTED REGION END #    //  SKASubarray.test_adminMode

    # PROTECTED REGION ID(SKASubarray.test_buildState_decorators) ENABLED START #
    # PROTECTED REGION END #    //  SKASubarray.test_buildState_decorators
    def test_buildState(self, tango_context):
        """Test for buildState"""
        # PROTECTED REGION ID(SKASubarray.test_buildState) ENABLED START #
        buildPattern = re.compile(
            r'lmcbaseclasses, [0-9].[0-9].[0-9], '
            r'A set of generic base devices for SKA Telescope')
        assert (re.match(buildPattern, tango_context.device.buildState)) is not None
        # PROTECTED REGION END #    //  SKASubarray.test_buildState

    # PROTECTED REGION ID(SKASubarray.test_configurationDelayExpected_decorators) ENABLED START #
    # PROTECTED REGION END #    //  SKASubarray.test_configurationDelayExpected_decorators
    def test_configurationDelayExpected(self, tango_context):
        """Test for configurationDelayExpected"""
        # PROTECTED REGION ID(SKASubarray.test_configurationDelayExpected) ENABLED START #
        assert tango_context.device.configurationDelayExpected == 0
        # PROTECTED REGION END #    //  SKASubarray.test_configurationDelayExpected

    # PROTECTED REGION ID(SKASubarray.test_configurationProgress_decorators) ENABLED START #
    # PROTECTED REGION END #    //  SKASubarray.test_configurationProgress_decorators
    def test_configurationProgress(self, tango_context):
        """Test for configurationProgress"""
        # PROTECTED REGION ID(SKASubarray.test_configurationProgress) ENABLED START #
        assert tango_context.device.configurationProgress == 0
        # PROTECTED REGION END #    //  SKASubarray.test_configurationProgress

    # PROTECTED REGION ID(SKASubarray.test_controlMode_decorators) ENABLED START #
    # PROTECTED REGION END #    //  SKASubarray.test_controlMode_decorators
    def test_controlMode(self, tango_context):
        """Test for controlMode"""
        # PROTECTED REGION ID(SKASubarray.test_controlMode) ENABLED START #
        assert tango_context.device.controlMode == ControlMode.REMOTE
        # PROTECTED REGION END #    //  SKASubarray.test_controlMode

    # PROTECTED REGION ID(SKASubarray.test_healthState_decorators) ENABLED START #
    # PROTECTED REGION END #    //  SKASubarray.test_healthState_decorators
    def test_healthState(self, tango_context):
        """Test for healthState"""
        # PROTECTED REGION ID(SKASubarray.test_healthState) ENABLED START #
        assert tango_context.device.healthState == HealthState.OK
        # PROTECTED REGION END #    //  SKASubarray.test_healthState

    # PROTECTED REGION ID(SKASubarray.test_obsMode_decorators) ENABLED START #
    # PROTECTED REGION END #    //  SKASubarray.test_obsMode_decorators
    def test_obsMode(self, tango_context):
        """Test for obsMode"""
        # PROTECTED REGION ID(SKASubarray.test_obsMode) ENABLED START #
        assert tango_context.device.obsMode == ObsMode.IDLE
        # PROTECTED REGION END #    //  SKASubarray.test_obsMode

    # PROTECTED REGION ID(SKASubarray.test_obsState_decorators) ENABLED START #
    # PROTECTED REGION END #    //  SKASubarray.test_obsState_decorators
    def test_obsState(self, tango_context):
        """Test for obsState"""
        # PROTECTED REGION ID(SKASubarray.test_obsState) ENABLED START #
        assert tango_context.device.obsState == ObsState.IDLE
        # PROTECTED REGION END #    //  SKASubarray.test_obsState

    # PROTECTED REGION ID(SKASubarray.test_simulationMode_decorators) ENABLED START #
    # PROTECTED REGION END #    //  SKASubarray.test_simulationMode_decorators
    def test_simulationMode(self, tango_context):
        """Test for simulationMode"""
        # PROTECTED REGION ID(SKASubarray.test_simulationMode) ENABLED START #
        assert tango_context.device.simulationMode == SimulationMode.FALSE
        # PROTECTED REGION END #    //  SKASubarray.test_simulationMode

    # PROTECTED REGION ID(SKASubarray.test_testMode_decorators) ENABLED START #
    # PROTECTED REGION END #    //  SKASubarray.test_testMode_decorators
    def test_testMode(self, tango_context):
        """Test for testMode"""
        # PROTECTED REGION ID(SKASubarray.test_testMode) ENABLED START #
        assert tango_context.device.testMode == TestMode.NONE
        # PROTECTED REGION END #    //  SKASubarray.test_testMode

    # PROTECTED REGION ID(SKASubarray.test_versionId_decorators) ENABLED START #
    # PROTECTED REGION END #    //  SKASubarray.test_versionId_decorators
    def test_versionId(self, tango_context):
        """Test for versionId"""
        # PROTECTED REGION ID(SKASubarray.test_versionId) ENABLED START #
        versionIdPattern = re.compile(r'[0-9].[0-9].[0-9]')
        assert (re.match(versionIdPattern, tango_context.device.versionId)) is not None
        # PROTECTED REGION END #    //  SKASubarray.test_versionId

    # PROTECTED REGION ID(SKASubarray.test_assignedResources_decorators) ENABLED START #
    # PROTECTED REGION END #    //  SKASubarray.test_assignedResources_decorators
    def test_assignedResources(self, tango_context):
        """Test for assignedResources"""
        # PROTECTED REGION ID(SKASubarray.test_assignedResources) ENABLED START #
        assert tango_context.device.assignedResources == None
        # PROTECTED REGION END #    //  SKASubarray.test_assignedResources

    # PROTECTED REGION ID(SKASubarray.test_configuredCapabilities_decorators) ENABLED START #
    # PROTECTED REGION END #    //  SKASubarray.test_configuredCapabilities_decorators
    def test_configuredCapabilities(self, tango_context):
        """Test for configuredCapabilities"""
        # PROTECTED REGION ID(SKASubarray.test_configuredCapabilities) ENABLED START #
        assert tango_context.device.configuredCapabilities == ("BAND1:0", "BAND2:0")
        # PROTECTED REGION END #    //  SKASubarray.test_configuredCapabilities

    @pytest.mark.parametrize(
        'state_under_test, action_under_test',
        itertools.product(
            ["DISABLED (NOTFITTED)", "DISABLED (OFFLINE)", "OFF (ONLINE)",
             "OFF (MAINTENANCE)", "ON (ONLINE)", "ON (MAINTENANCE)",
             "READY (ONLINE)", "READY (MAINTENANCE)", "SCANNING (ONLINE)",
             "SCANNING (MAINTENANCE)", "ABORTED (ONLINE)",
             "ABORTED (MAINTENANCE)"],
            ["notfitted", "offline", "online", "maintenance", "assign",
             "release", "release (all)", "releaseall", "configure",
             "deconfigure", "deconfigure (all)", "deconfigureall",
             "deconfigureall (all)", "scan", "endscan", "endsb", "abort",
             "reset"]
        )
    )
    def test_state_machine(self, tango_context,
                           state_under_test, action_under_test):
        """
        Test the subarray state machine: for a given initial state and
        an action, does execution of that action, from that initial
        state, yield the expected results? If the action was not allowed
        from that initial state, does the device raise a DevFailed
        exception? If the action was allowed, does it result in the
        correct state transition?
        """

        states = {
            "DISABLED (NOTFITTED)":
                (AdminMode.NOT_FITTED, DevState.DISABLE, ObsState.IDLE),
            "DISABLED (OFFLINE)":
                (AdminMode.OFFLINE, DevState.DISABLE, ObsState.IDLE),
            "OFF (ONLINE)":
                (AdminMode.ONLINE, DevState.OFF, ObsState.IDLE),
            "OFF (MAINTENANCE)":
                (AdminMode.MAINTENANCE, DevState.OFF, ObsState.IDLE),
            "ON (ONLINE)":
                (AdminMode.ONLINE, DevState.ON, ObsState.IDLE),
            "ON (MAINTENANCE)":
                (AdminMode.MAINTENANCE, DevState.ON, ObsState.IDLE),
            "READY (ONLINE)":
                (AdminMode.ONLINE, DevState.ON, ObsState.READY),
            "READY (MAINTENANCE)":
                (AdminMode.MAINTENANCE, DevState.ON, ObsState.READY),
            "SCANNING (ONLINE)":
                (AdminMode.ONLINE, DevState.ON, ObsState.SCANNING),
            "SCANNING (MAINTENANCE)":
                (AdminMode.MAINTENANCE, DevState.ON, ObsState.SCANNING),
            "ABORTED (ONLINE)":
                (AdminMode.ONLINE, DevState.ON, ObsState.ABORTED),
            "ABORTED (MAINTENANCE)":
                (AdminMode.MAINTENANCE, DevState.ON, ObsState.ABORTED),
        }

        def assert_state(state):
            assert states[state] == (tango_context.device.adminMode,
                                     tango_context.device.state(),
                                     tango_context.device.obsState)

        actions = {
            "notfitted":
                lambda d: d.write_attribute("adminMode", AdminMode.NOT_FITTED),
            "offline":
                lambda d: d.write_attribute("adminMode", AdminMode.OFFLINE),
            "online":
                lambda d: d.write_attribute("adminMode", AdminMode.ONLINE),
            "maintenance":
                lambda d: d.write_attribute("adminMode", AdminMode.MAINTENANCE),
            "assign":
                lambda d: d.AssignResources(
                    ["Dummy resource 1", "Dummy resource 2"]
                ),
            "release":
                lambda d: d.ReleaseResources(["Dummy resource 2"]),
            "release (all)":
                lambda d: d.ReleaseResources(
                    ["Dummy resource 1", "Dummy resource 2"]
                ),
            "releaseall":
                lambda d: d.ReleaseAllResources(),
            "configure":
                lambda d: d.ConfigureCapability([[2, 2], ["BAND1", "BAND2"]]),
            "deconfigure":
                lambda d: d.DeconfigureCapability([[1], ["BAND1"]]),
            "deconfigure (all)":
                lambda d: d.DeconfigureCapability([[2, 2], ["BAND1", "BAND2"]]),
            "deconfigureall":
                lambda d: d.DeconfigureAllCapabilities("BAND1"),
            "deconfigureall (all)":
                lambda d: [d.DeconfigureAllCapabilities("BAND1"),
                           d.DeconfigureAllCapabilities("BAND2")],
            "scan":
                lambda d: d.Scan(["Dummy scan id"]),
            "endscan":
                lambda d: d.EndScan(),
            "endsb":
                lambda d: d.EndSB(),
            "abort":
                lambda d: d.Abort(),
            "reset":
                lambda d: d.Reset(),
        }

        def perform_action(action):
            actions[action](tango_context.device)

        transitions = {
            ("DISABLED (NOTFITTED)", "notfitted"): "DISABLED (NOTFITTED)",
            ("DISABLED (NOTFITTED)", "offline"): "DISABLED (OFFLINE)",
            ("DISABLED (NOTFITTED)", "online"): "OFF (ONLINE)",
            ("DISABLED (NOTFITTED)", "maintenance"): "OFF (MAINTENANCE)",
            ("DISABLED (OFFLINE)", "notfitted"): "DISABLED (NOTFITTED)",
            ("DISABLED (OFFLINE)", "offline"): "DISABLED (OFFLINE)",
            ("DISABLED (OFFLINE)", "online"): "OFF (ONLINE)",
            ("DISABLED (OFFLINE)", "maintenance"): "OFF (MAINTENANCE)",
            ("OFF (ONLINE)", "notfitted"): "DISABLED (NOTFITTED)",
            ("OFF (ONLINE)", "offline"): "DISABLED (OFFLINE)",
            ("OFF (ONLINE)", "online"): "OFF (ONLINE)",
            ("OFF (ONLINE)", "maintenance"): "OFF (MAINTENANCE)",
            ("OFF (ONLINE)", "assign"): "ON (ONLINE)",
            ("OFF (MAINTENANCE)", "notfitted"): "DISABLED (NOTFITTED)",
            ("OFF (MAINTENANCE)", "offline"): "DISABLED (OFFLINE)",
            ("OFF (MAINTENANCE)", "online"): "OFF (ONLINE)",
            ("OFF (MAINTENANCE)", "maintenance"): "OFF (MAINTENANCE)",
            ("OFF (MAINTENANCE)", "assign"): "ON (MAINTENANCE)",
            ("ON (ONLINE)", "notfitted"): "DISABLED (NOTFITTED)",
            ("ON (ONLINE)", "offline"): "DISABLED (OFFLINE)",
            ("ON (ONLINE)", "online"): "ON (ONLINE)",
            ("ON (ONLINE)", "maintenance"): "ON (MAINTENANCE)",
            ("ON (ONLINE)", "assign"): "ON (ONLINE)",
            ("ON (ONLINE)", "release"): "ON (ONLINE)",
            ("ON (ONLINE)", "release (all)"): "OFF (ONLINE)",
            ("ON (ONLINE)", "releaseall"): "OFF (ONLINE)",
            ("ON (ONLINE)", "configure"): "READY (ONLINE)",
            ("ON (MAINTENANCE)", "notfitted"): "DISABLED (NOTFITTED)",
            ("ON (MAINTENANCE)", "offline"): "DISABLED (OFFLINE)",
            ("ON (MAINTENANCE)", "online"): "ON (ONLINE)",
            ("ON (MAINTENANCE)", "maintenance"): "ON (MAINTENANCE)",
            ("ON (MAINTENANCE)", "assign"): "ON (MAINTENANCE)",
            ("ON (MAINTENANCE)", "release"): "ON (MAINTENANCE)",
            ("ON (MAINTENANCE)", "release (all)"): "OFF (MAINTENANCE)",
            ("ON (MAINTENANCE)", "releaseall"): "OFF (MAINTENANCE)",
            ("ON (MAINTENANCE)", "configure"): "READY (MAINTENANCE)",
            ("READY (ONLINE)", "notfitted"): "DISABLED (NOTFITTED)",
            ("READY (ONLINE)", "offline"): "DISABLED (OFFLINE)",
            ("READY (ONLINE)", "online"): "READY (ONLINE)",
            ("READY (ONLINE)", "maintenance"): "READY (MAINTENANCE)",
            ("READY (ONLINE)", "endsb"): "ON (ONLINE)",
            ("READY (ONLINE)", "reset"): "ON (ONLINE)",
            ("READY (ONLINE)", "configure"): "READY (ONLINE)",
            ("READY (ONLINE)", "deconfigure"): "READY (ONLINE)",
            ("READY (ONLINE)", "deconfigure (all)"): "ON (ONLINE)",
            ("READY (ONLINE)", "deconfigureall"): "READY (ONLINE)",
            ("READY (ONLINE)", "deconfigureall (all)"): "ON (ONLINE)",
            ("READY (ONLINE)", "scan"): "SCANNING (ONLINE)",
            ("READY (ONLINE)", "abort"): "ABORTED (ONLINE)",
            ("READY (MAINTENANCE)", "notfitted"): "DISABLED (NOTFITTED)",
            ("READY (MAINTENANCE)", "offline"): "DISABLED (OFFLINE)",
            ("READY (MAINTENANCE)", "online"): "READY (ONLINE)",
            ("READY (MAINTENANCE)", "maintenance"): "READY (MAINTENANCE)",
            ("READY (MAINTENANCE)", "endsb"): "ON (MAINTENANCE)",
            ("READY (MAINTENANCE)", "reset"): "ON (MAINTENANCE)",
            ("READY (MAINTENANCE)", "configure"): "READY (MAINTENANCE)",
            ("READY (MAINTENANCE)", "deconfigure"): "READY (MAINTENANCE)",
            ("READY (MAINTENANCE)", "deconfigure (all)"): "ON (MAINTENANCE)",
            ("READY (MAINTENANCE)", "deconfigureall"): "READY (MAINTENANCE)",
            ("READY (MAINTENANCE)", "deconfigureall (all)"): "ON (MAINTENANCE)",
            ("READY (MAINTENANCE)", "scan"): "SCANNING (MAINTENANCE)",
            ("READY (MAINTENANCE)", "abort"): "ABORTED (MAINTENANCE)",
            ("SCANNING (ONLINE)", "notfitted"): "DISABLED (NOTFITTED)",
            ("SCANNING (ONLINE)", "offline"): "DISABLED (OFFLINE)",
            ("SCANNING (ONLINE)", "online"): "SCANNING (ONLINE)",
            ("SCANNING (ONLINE)", "maintenance"): "SCANNING (MAINTENANCE)",
            ("SCANNING (ONLINE)", "endscan"): "READY (ONLINE)",
            ("SCANNING (ONLINE)", "abort"): "ABORTED (ONLINE)",
            ("SCANNING (ONLINE)", "reset"): "ON (ONLINE)",
            ("SCANNING (MAINTENANCE)", "notfitted"): "DISABLED (NOTFITTED)",
            ("SCANNING (MAINTENANCE)", "offline"): "DISABLED (OFFLINE)",
            ("SCANNING (MAINTENANCE)", "online"): "SCANNING (ONLINE)",
            ("SCANNING (MAINTENANCE)", "maintenance"): "SCANNING (MAINTENANCE)",
            ("SCANNING (MAINTENANCE)", "endscan"): "READY (MAINTENANCE)",
            ("SCANNING (MAINTENANCE)", "abort"): "ABORTED (MAINTENANCE)",
            ("SCANNING (MAINTENANCE)", "reset"): "ON (MAINTENANCE)",
            ("ABORTED (ONLINE)", "notfitted"): "DISABLED (NOTFITTED)",
            ("ABORTED (ONLINE)", "offline"): "DISABLED (OFFLINE)",
            ("ABORTED (ONLINE)", "online"): "ABORTED (ONLINE)",
            ("ABORTED (ONLINE)", "maintenance"): "ABORTED (MAINTENANCE)",
            ("ABORTED (ONLINE)", "reset"): "ON (ONLINE)",
            ("ABORTED (MAINTENANCE)", "notfitted"): "DISABLED (NOTFITTED)",
            ("ABORTED (MAINTENANCE)", "offline"): "DISABLED (OFFLINE)",
            ("ABORTED (MAINTENANCE)", "online"): "ABORTED (ONLINE)",
            ("ABORTED (MAINTENANCE)", "maintenance"): "ABORTED (MAINTENANCE)",
            ("ABORTED (MAINTENANCE)", "reset"): "ON (MAINTENANCE)",
        }

        setups = {
            "DISABLED (NOTFITTED)":
                ['notfitted'],
            "DISABLED (OFFLINE)":
                ['offline'],
            "OFF (ONLINE)":
                ['online'],
            "OFF (MAINTENANCE)":
                ['maintenance'],
            "ON (ONLINE)":
                ['online', 'assign'],
            "ON (MAINTENANCE)":
                ['maintenance', 'assign'],
            "READY (ONLINE)":
                ['online', 'assign', 'configure'],
            "READY (MAINTENANCE)":
                ['maintenance', 'assign', 'configure'],
            "SCANNING (ONLINE)":
                ['online', 'assign', 'configure', 'scan'],
            "SCANNING (MAINTENANCE)":
                ['maintenance', 'assign', 'configure', 'scan'],
            "ABORTED (ONLINE)":
                ['online', 'assign', 'configure', 'abort'],
            "ABORTED (MAINTENANCE)":
                ['maintenance', 'assign', 'configure', 'abort'],
        }

        # bypass cache for this test because we are testing for a change
        # in the polled attribute obsState
        tango_context.device.set_source(DevSource.DEV)

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
            # Action should fail
            with pytest.raises(DevFailed):
                perform_action(action_under_test)
