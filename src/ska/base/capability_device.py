# -*- coding: utf-8 -*-
#
# This file is part of the SKACapability project
#
#
#
""" SKACapability

Capability handling device
"""
# PROTECTED REGION ID(SKACapability.additionnal_import) ENABLED START #
# Tango imports
from tango import DebugIt
from tango.server import run, attribute, command, device_property

# SKA specific imports
from ska.base import SKAObsDevice
from ska.base.control_model import ReturnCode
# PROTECTED REGION END #    //  SKACapability.additionnal_imports

__all__ = ["SKACapability", "main"]


class SKACapability(SKAObsDevice):
    """
    A Subarray handling device. It exposes the instances of configured capabilities.
    """
    class InitCommand(SKAObsDevice.InitCommand):
        def do(self, target):
            """
            Stateless hook for device initialisation.

            :param target: the object that this command acts upon; for
                example, the SKASubarray device for which this class
                implements the command
            :type target: object
            :return: A tuple containing a return code and a string
                message indicating status. The message is for
                information purpose only.
            :rtype: (ReturnCode, str)
            """
            (return_code, message) = super().do(target)

            target._activation_time = 0.0
            target._configured_instances = 0
            target._used_components = [""]

            message = "SKACapability initialisation completed OK"
            self.logger.info(message)
            return (ReturnCode.OK, message)

    # PROTECTED REGION ID(SKACapability.class_variable) ENABLED START #
    # PROTECTED REGION END #    //  SKACapability.class_variable

    # -----------------
    # Device Properties
    # -----------------

    CapType = device_property(
        dtype='str',
    )

    CapID = device_property(
        dtype='str',
    )

    subID = device_property(
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

    configuredInstances = attribute(
        dtype='uint16',
        doc="Number of instances of this Capability Type currently in use on this subarray.",
    )

    usedComponents = attribute(
        dtype=('str',),
        max_dim_x=100,
        doc="A list of components with no. of instances in use on this Capability.",
    )

    # ---------------
    # General methods
    # ---------------

    def always_executed_hook(self):
        # PROTECTED REGION ID(SKACapability.always_executed_hook) ENABLED START #
        pass
        # PROTECTED REGION END #    //  SKACapability.always_executed_hook

    def delete_device(self):
        # PROTECTED REGION ID(SKACapability.delete_device) ENABLED START #
        pass
        # PROTECTED REGION END #    //  SKACapability.delete_device

    # ------------------
    # Attributes methods
    # ------------------

    def read_activationTime(self):
        # PROTECTED REGION ID(SKACapability.activationTime_read) ENABLED START #
        """
        Reads time of activation since Unix epoch.
        :return: Activation time in seconds
        """
        return self._activation_time
        # PROTECTED REGION END #    //  SKACapability.activationTime_read

    def read_configuredInstances(self):
        # PROTECTED REGION ID(SKACapability.configuredInstances_read) ENABLED START #
        """
        Reads the number of instances of a capability in the subarray
        :return: The number of configured instances of a capability in a subarray
        """
        return self._configured_instances
        # PROTECTED REGION END #    //  SKACapability.configuredInstances_read

    def read_usedComponents(self):
        # PROTECTED REGION ID(SKACapability.usedComponents_read) ENABLED START #
        """
        Reads the list of components with no. of instances in use on this Capability
        :return: The number of components currently in use.
        """
        return self._used_components
        # PROTECTED REGION END #    //  SKACapability.usedComponents_read

    # --------
    # Commands
    # --------

    @command(
        dtype_in='uint16',
        doc_in="The number of instances to configure for this Capability.",
    )
    @DebugIt()
    def ConfigureInstances(self, argin):
        # PROTECTED REGION ID(SKACapability.ConfigureInstances) ENABLED START #
        """
        This function indicates how many number of instances of the current capacity
        should to be configured.
        :param argin: Number of instances to configure
        :return: None.
        """
        self._configured_instances = argin
        # PROTECTED REGION END #    //  SKACapability.ConfigureInstances


# ----------
# Run server
# ----------

def main(args=None, **kwargs):
    # PROTECTED REGION ID(SKACapability.main) ENABLED START #
    """Main function of the SKACapability module."""
    return run((SKACapability,), args=args, **kwargs)
    # PROTECTED REGION END #    //  SKACapability.main


if __name__ == '__main__':
    main()
