# -*- coding: utf-8 -*-
#
# This file is part of the SKALogger project
#
#
#
"""
This module implements SKALogger device, a generic base device for
logging for SKA. It enables to view on-line logs through the TANGO
Logging Services and to store logs using Python logging. It configures
the log levels of remote logging for selected devices.
"""
# PROTECTED REGION ID(SKALogger.additionnal_import) ENABLED START #
# Tango imports
from tango import DebugIt, DeviceProxy, DevFailed
from tango.server import run, command

# SKA specific imports
from ska.base import SKABaseDevice
from ska.base.commands import ActionCommand, ReturnCode
from ska.base.control_model import LoggingLevel
# PROTECTED REGION END #    //  SKALogger.additionnal_import

__all__ = ["SKALogger", "main"]


class SKALogger(SKABaseDevice):
    """
    A generic base device for Logging for SKA.
    """
    # PROTECTED REGION ID(SKALogger.class_variable) ENABLED START #
    # PROTECTED REGION END #    //  SKALogger.class_variable

    # -----------------
    # Device Properties
    # -----------------

    # ----------
    # Attributes
    # ----------

    # ---------------
    # General methods
    # ---------------
    def _init_command_objects(self):
        """
        Sets up the command objects
        """
        super()._init_command_objects()
        self._set_logging_level_command = self.SetLoggingLevelCommand(
            None, self.state_model, self.logger
        )

    def always_executed_hook(self):
        # PROTECTED REGION ID(SKALogger.always_executed_hook) ENABLED START #
        pass
        # PROTECTED REGION END #    //  SKALogger.always_executed_hook

    def delete_device(self):
        # PROTECTED REGION ID(SKALogger.delete_device) ENABLED START #
        pass
        # PROTECTED REGION END #    //  SKALogger.delete_device

    # ------------------
    # Attributes methods
    # ------------------

    # --------
    # Commands
    # --------
    class SetLoggingLevelCommand(ActionCommand):
        """
        A class for the SKALoggerDevice's SetLoggingLevel() command.
        """
        def __init__(self, target, state_model, logger=None):
            """
            Constructor for SetLoggingLevelCommand

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
            super().__init__(target, state_model, logger=logger)

        def do(self, target, argin):
            """
            Stateless hook for SetLoggingLevel() command functionality.

            :param target: the object that this command acts upon; for
                example, the SKALogger device for which this class
                implements the command
            :type target: object
            :return: A tuple containing a return code and a string
                message indicating status. The message is for
                information purpose only.
            :rtype: (ReturnCode, str)
            """
            logging_levels = argin[0][:]
            logging_devices = argin[1][:]
            for level, device in zip(logging_levels, logging_devices):
                try:
                    new_level = LoggingLevel(level)
                    self.logger.info("Setting logging level %s for %s", new_level, device)
                    dev_proxy = DeviceProxy(device)
                    dev_proxy.loggingLevel = new_level
                except DevFailed:
                    self.logger.exception("Failed to set logging level %s for %s", level, device)

            message = "SetLoggingLevel command completed OK"
            self.logger.info(message)
            return (ReturnCode.OK, message)

    @command(dtype_in='DevVarLongStringArray',
             doc_in="Logging level for selected devices:"
                    "(0=OFF, 1=FATAL, 2=ERROR, 3=WARNING, 4=INFO, 5=DEBUG)."
                    "Example: [[4, 5], ['my/dev/1', 'my/dev/2']].")
    @DebugIt()
    def SetLoggingLevel(self, argin):
        # PROTECTED REGION ID(SKALogger.SetLoggingLevel) ENABLED START #
        """
        Sets logging level of the specified devices.

        :parameter: argin: DevVarLongStringArray
            Array consisting of

            argin[0]: list of DevLong. Desired logging level.

            argin[1]: list of DevString. Desired tango device.

        :returns: None.
        """
        self._set_logging_level_command(argin)
        # PROTECTED REGION END #    //  SKALogger.SetLoggingLevel

# ----------
# Run server
# ----------


def main(args=None, **kwargs):
    # PROTECTED REGION ID(SKALogger.main) ENABLED START #
    """
    Main entry point of the module.
    """
    return run((SKALogger,), args=args, **kwargs)
    # PROTECTED REGION END #    //  SKALogger.main


if __name__ == '__main__':
    main()
