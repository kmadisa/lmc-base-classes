# -*- coding: utf-8 -*-
#
# This file is part of the SKAMaster project
#
#
#

""" SKAMaster

Master device
"""
# PROTECTED REGION ID(SKAMaster.additionnal_import) ENABLED START #
# Tango imports
from tango import DebugIt
from tango.server import run, attribute, command, device_property

# SKA specific imports
from ska.base import SKABaseDevice
from ska.base.utils import validate_capability_types, validate_input_sizes, convert_dict_to_list


# PROTECTED REGION END #    //  SKAMaster.additionnal_imports

__all__ = ["SKAMaster", "main"]


class SKAMaster(SKABaseDevice):
    """
    Master device
    """
    class InitCommand(SKABaseDevice.InitCommand):
        """
        A class for the SKAMaster's init_device() "command".
        """
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

            target._element_logger_address = ""
            target._element_alarm_address = ""
            target._element_tel_state_address = ""
            target._element_database_address = ""
            target._element_alarm_device = ""
            target._element_tel_state_device = ""
            target._element_database_device = ""
            target._max_capabilities = {}
            if target.MaxCapabilities:
                for max_capability in target.MaxCapabilities:
                    capability_type, max_capability_instances = max_capability.split(":")
                    target._max_capabilities[capability_type] = int(max_capability_instances)
            target._available_capabilities = target._max_capabilities.copy()

            return (return_code, message)

    # PROTECTED REGION ID(SKAMaster.class_variable) ENABLED START #
    # PROTECTED REGION END #    //  SKAMaster.class_variable

    # -----------------
    # Device Properties
    # -----------------

    # List of maximum number of instances per capability type provided by this Element;
    # CORRELATOR=512, PSS-BEAMS=4, PST-BEAMS=6, VLBI-BEAMS=4  or for DSH it can be:
    # BAND-1=1, BAND-2=1, BAND3=0, BAND-4=0, BAND-5=0 (if only bands 1&amp;2 is installed)
    MaxCapabilities = device_property(
        dtype=('str',),
    )

    # ----------
    # Attributes
    # ----------

    elementLoggerAddress = attribute(
        dtype='str',
        doc="FQDN of Element Logger",
    )

    elementAlarmAddress = attribute(
        dtype='str',
        doc="FQDN of Element Alarm Handlers",
    )

    elementTelStateAddress = attribute(
        dtype='str',
        doc="FQDN of Element TelState device",
    )

    elementDatabaseAddress = attribute(
        dtype='str',
        doc="FQDN of Element Database device",
    )

    maxCapabilities = attribute(
        dtype=('str',),
        max_dim_x=20,
        doc=("Maximum number of instances of each capability type,"
             " e.g. 'CORRELATOR:512', 'PSS-BEAMS:4'."),
    )

    availableCapabilities = attribute(
        dtype=('str',),
        max_dim_x=20,
        doc="A list of available number of instances of each capability type, "
            "e.g. 'CORRELATOR:512', 'PSS-BEAMS:4'.",
    )

    # ---------------
    # General methods
    # ---------------

    def always_executed_hook(self):
        # PROTECTED REGION ID(SKAMaster.always_executed_hook) ENABLED START #
        pass
        # PROTECTED REGION END #    //  SKAMaster.always_executed_hook

    def delete_device(self):
        # PROTECTED REGION ID(SKAMaster.delete_device) ENABLED START #
        pass
        # PROTECTED REGION END #    //  SKAMaster.delete_device

    # ------------------
    # Attributes methods
    # ------------------

    def read_elementLoggerAddress(self):
        # PROTECTED REGION ID(SKAMaster.elementLoggerAddress_read) ENABLED START #
        """Reads FQDN of Element Logger device"""
        return self._element_logger_address
        # PROTECTED REGION END #    //  SKAMaster.elementLoggerAddress_read

    def read_elementAlarmAddress(self):
        # PROTECTED REGION ID(SKAMaster.elementAlarmAddress_read) ENABLED START #
        """Reads FQDN of Element Alarm device"""
        return self._element_alarm_address
        # PROTECTED REGION END #    //  SKAMaster.elementAlarmAddress_read

    def read_elementTelStateAddress(self):
        # PROTECTED REGION ID(SKAMaster.elementTelStateAddress_read) ENABLED START #
        """Reads FQDN of Element TelState device"""
        return self._element_tel_state_address
        # PROTECTED REGION END #    //  SKAMaster.elementTelStateAddress_read

    def read_elementDatabaseAddress(self):
        # PROTECTED REGION ID(SKAMaster.elementDatabaseAddress_read) ENABLED START #
        """Reads FQDN of Element Database device"""
        return self._element_database_address
        # PROTECTED REGION END #    //  SKAMaster.elementDatabaseAddress_read

    def read_maxCapabilities(self):
        # PROTECTED REGION ID(SKAMaster.maxCapabilities_read) ENABLED START #
        """Reads maximum number of instances of each capability type"""
        return convert_dict_to_list(self._max_capabilities)
        # PROTECTED REGION END #    //  SKAMaster.maxCapabilities_read

    def read_availableCapabilities(self):
        # PROTECTED REGION ID(SKAMaster.availableCapabilities_read) ENABLED START #
        """Reads list of available number of instances of each capability type"""
        return convert_dict_to_list(self._available_capabilities)
        # PROTECTED REGION END #    //  SKAMaster.availableCapabilities_read

    # --------
    # Commands
    # --------

    @command(
        dtype_in='DevVarLongStringArray',
        doc_in="[nrInstances][Capability types]",
        dtype_out='bool',
    )
    @DebugIt()
    def isCapabilityAchievable(self, argin):
        # PROTECTED REGION ID(SKAMaster.isCapabilityAchievable) ENABLED START #
        """
        Checks of provided capabilities can be achieved by the resource(s).

        :param argin: DevVarLongStringArray.

            An array consisting pair of
                    [nrInstances]: DevLong. Number of instances of the capability.

                    [Capability types]: DevString. Type of capability.

        :return: DevBoolean

            True if capability can be achieved.

            False if cannot.
        """
        command_name = 'isCapabilityAchievable'
        capabilities_instances, capability_types = argin
        validate_input_sizes(command_name, argin)
        validate_capability_types(command_name, capability_types,
                                  list(self._max_capabilities.keys()))

        for capability_type, capability_instances in zip(
                capability_types, capabilities_instances):
            if not self._available_capabilities[capability_type] >= capability_instances:
                return False

        return True
        # PROTECTED REGION END #    //  SKAMaster.isCapabilityAchievable


# ----------
# Run server
# ----------
def main(args=None, **kwargs):
    # PROTECTED REGION ID(SKAMaster.main) ENABLED START #
    return run((SKAMaster,), args=args, **kwargs)
    # PROTECTED REGION END #    //  SKAMaster.main


if __name__ == '__main__':
    main()
