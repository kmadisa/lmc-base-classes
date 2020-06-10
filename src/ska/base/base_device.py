# -*- coding: utf-8 -*-
#
# This file is part of the SKABaseDevice project
#
#
#

"""A generic base device for SKA. It exposes the generic attributes,
properties and commands of an SKA device.
"""
# PROTECTED REGION ID(SKABaseDevice.additionnal_import) ENABLED START #
# Standard imports
import enum
import inspect
import logging
import logging.handlers
import socket
import sys
import threading
import warnings

from urllib.parse import urlparse
from urllib.request import url2pathname

# Tango imports
from tango import DebugIt
from tango.server import run, Device, attribute, command, device_property
from tango import AttrWriteType
from tango import DevState

# SKA specific imports
import ska.logging as ska_logging
from ska.base import release
from ska.base.control_model import (
    AdminMode, ControlMode, SimulationMode, TestMode,
    HealthState, LoggingLevel, ReturnCode,
    guard
)

from ska.base.utils import get_groups_from_json
from ska.base.faults import (GroupDefinitionsError,
                             LoggingTargetError,
                             LoggingLevelError)

LOG_FILE_SIZE = 1024 * 1024  # Log file size 1MB.


class _Log4TangoLoggingLevel(enum.IntEnum):
    """Python enumerated type for TANGO log4tango logging levels.

    This is different to tango.LogLevel, and is required if using
    a device's set_log_level() method.  It is not currently exported
    via PyTango, so we hard code it here in the interim.

    Source:
       https://github.com/tango-controls/cppTango/blob/
       4feffd7c8e24b51c9597a40b9ef9982dd6e99cdf/log4tango/include/log4tango/Level.hh#L86-L93
    """
    OFF = 100
    FATAL = 200
    ERROR = 300
    WARN = 400
    INFO = 500
    DEBUG = 600


_PYTHON_TO_TANGO_LOGGING_LEVEL = {
    logging.CRITICAL: _Log4TangoLoggingLevel.FATAL,
    logging.ERROR: _Log4TangoLoggingLevel.ERROR,
    logging.WARNING: _Log4TangoLoggingLevel.WARN,
    logging.INFO: _Log4TangoLoggingLevel.INFO,
    logging.DEBUG: _Log4TangoLoggingLevel.DEBUG,
}

_LMC_TO_TANGO_LOGGING_LEVEL = {
    LoggingLevel.OFF: _Log4TangoLoggingLevel.OFF,
    LoggingLevel.FATAL: _Log4TangoLoggingLevel.FATAL,
    LoggingLevel.ERROR: _Log4TangoLoggingLevel.ERROR,
    LoggingLevel.WARNING: _Log4TangoLoggingLevel.WARN,
    LoggingLevel.INFO: _Log4TangoLoggingLevel.INFO,
    LoggingLevel.DEBUG: _Log4TangoLoggingLevel.DEBUG,
}

_LMC_TO_PYTHON_LOGGING_LEVEL = {
    LoggingLevel.OFF: logging.CRITICAL,  # there is no "off"
    LoggingLevel.FATAL: logging.CRITICAL,
    LoggingLevel.ERROR: logging.ERROR,
    LoggingLevel.WARNING: logging.WARNING,
    LoggingLevel.INFO: logging.INFO,
    LoggingLevel.DEBUG: logging.DEBUG,
}


class TangoLoggingServiceHandler(logging.Handler):
    """Handler that emit logs via Tango device's logger to TLS."""

    def __init__(self, tango_logger):
        super().__init__()
        self.tango_logger = tango_logger

    def emit(self, record):
        try:
            msg = self.format(record)
            tango_level = _PYTHON_TO_TANGO_LOGGING_LEVEL[record.levelno]
            self.acquire()
            try:
                self.tango_logger.log(tango_level, msg)
            finally:
                self.release()
        except Exception:
            self.handleError(record)

    def __repr__(self):
        python_level = logging.getLevelName(self.level)
        if self.tango_logger:
            tango_level = _Log4TangoLoggingLevel(self.tango_logger.get_level()).name
            name = self.tango_logger.get_name()
        else:
            tango_level = "UNKNOWN"
            name = "!No Tango logger!"
        return '<{} {} (Python {}, Tango {})>'.format(
            self.__class__.__name__, name, python_level, tango_level)


class LoggingUtils:
    """Utility functions to aid logger configuration.

    These functions are encapsulated in class to aid testing - it
    allows dependent functions to be mocked.
    """

    @staticmethod
    def sanitise_logging_targets(targets, device_name):
        """Validate and return logging targets '<type>::<name>' strings.

        :param target:
            List of candidate logging target strings, like '<type>[::<name>]'
            Empty and whitespace-only strings are ignored.  Can also be None.

        :param device_name:
            TANGO device name, like 'domain/family/member', used
            for the default file name

        :return: list of '<type>::<name>' strings, with default name, if applicable

        :raises: LoggingTargetError for invalid target string that cannot be corrected
        """
        default_target_names = {
            "console": "cout",
            "file": "{}.log".format(device_name.replace("/", "_")),
            "syslog": None,
            "tango": "logger",
        }

        valid_targets = []
        if targets:
            for target in targets:
                target = target.strip()
                if not target:
                    continue
                if "::" in target:
                    target_type, target_name = target.split("::", 1)
                else:
                    target_type = target
                    target_name = None
                if target_type not in default_target_names:
                    raise LoggingTargetError(
                        "Invalid target type: {} - options are {}".format(
                            target_type, list(default_target_names.keys())))
                if not target_name:
                    target_name = default_target_names[target_type]
                if not target_name:
                    raise LoggingTargetError(
                        "Target name required for type {}".format(target_type))
                valid_target = "{}::{}".format(target_type, target_name)
                valid_targets.append(valid_target)

        return valid_targets

    @staticmethod
    def get_syslog_address_and_socktype(url):
        """Parse syslog URL and extract address and socktype parameters for SysLogHandler.

        :param url:
            Universal resource locator string for syslog target.  Three types are supported:
            file path, remote UDP server, remote TCP server.
            - Output to a file:  'file://<path to file>'
              Example:  'file:///dev/log' will write to '/dev/log'
            - Output to remote server over UDP:  'udp://<hostname>:<port>'
              Example:  'udp://syslog.com:514' will send to host 'syslog.com' on UDP port 514
            - Output to remote server over TCP:  'tcp://<hostname>:<port>'
              Example:  'tcp://rsyslog.com:601' will send to host 'rsyslog.com' on TCP port 601
            For backwards compatibility, if the protocol prefix is missing, the type is
            interpreted as file.  This is deprecated.
            - Example:  '/dev/log' is equivalent to 'file:///dev/log'

        :return: (address, socktype)
            For file types:
            - address is the file path as as string
            - socktype is None
            For UDP and TCP:
            - address is tuple of (hostname, port), with hostname a string, and port an integer.
            - socktype is socket.SOCK_DGRAM for UDP, or socket.SOCK_STREAM for TCP.

        :raises: LoggingTargetError for invalid url string
        """
        address = None
        socktype = None
        parsed = urlparse(url)
        if parsed.scheme in ["file", ""]:
            address = url2pathname(parsed.netloc + parsed.path)
            socktype = None
            if not address:
                raise LoggingTargetError(
                    "Invalid syslog URL - empty file path from '{}'".format(url)
                )
            if parsed.scheme == "":
                warnings.warn(
                    "Specifying syslog URL without protocol is deprecated, "
                    "use 'file://{}' instead of '{}'".format(url, url),
                    DeprecationWarning,
                )
        elif parsed.scheme in ["udp", "tcp"]:
            if not parsed.hostname:
                raise LoggingTargetError(
                    "Invalid syslog URL - could not extract hostname from '{}'".format(url)
                )
            try:
                port = int(parsed.port)
            except (TypeError, ValueError):
                raise LoggingTargetError(
                    "Invalid syslog URL - could not extract integer port number from '{}'".format(
                        url
                    )
                )
            address = (parsed.hostname, port)
            socktype = socket.SOCK_DGRAM if parsed.scheme == "udp" else socket.SOCK_STREAM
        else:
            raise LoggingTargetError(
                "Invalid syslog URL - expected file, udp or tcp protocol scheme in '{}'".format(url)
            )
        return address, socktype

    @staticmethod
    def create_logging_handler(target, tango_logger=None):
        """Create a Python log handler based on the target type (console, file, syslog, tango)

        :param target:
            Logging target for logger, <type>::<name>

        :param tango_logger:
            Instance of tango.Logger, optional.  Only required if creating
            a target of type "tango".

        :return: StreamHandler, RotatingFileHandler, SysLogHandler, or TangoLoggingServiceHandler

        :raises: LoggingTargetError for invalid target string
        """
        if "::" in target:
            target_type, target_name = target.split("::", 1)
        else:
            raise LoggingTargetError(
                "Invalid target requested - missing '::' separator: {}".format(target))
        if target_type == "console":
            handler = logging.StreamHandler(sys.stdout)
        elif target_type == "file":
            log_file_name = target_name
            handler = logging.handlers.RotatingFileHandler(
                log_file_name, 'a', LOG_FILE_SIZE, 2, None, False)
        elif target_type == "syslog":
            address, socktype = LoggingUtils.get_syslog_address_and_socktype(target_name)
            handler = logging.handlers.SysLogHandler(
                address=address,
                facility=logging.handlers.SysLogHandler.LOG_SYSLOG,
                socktype=socktype)
        elif target_type == "tango":
            if tango_logger:
                handler = TangoLoggingServiceHandler(tango_logger)
            else:
                raise LoggingTargetError("Missing tango_logger instance for 'tango' target type")
        else:
            raise LoggingTargetError(
                "Invalid target type requested: '{}' in '{}'".format(target_type, target))
        formatter = ska_logging.get_default_formatter(tags=True)
        handler.setFormatter(formatter)
        handler.name = target
        return handler

    @staticmethod
    def update_logging_handlers(targets, logger):
        old_targets = [handler.name for handler in logger.handlers]
        added_targets = set(targets) - set(old_targets)
        removed_targets = set(old_targets) - set(targets)

        for handler in list(logger.handlers):
            if handler.name in removed_targets:
                logger.removeHandler(handler)
        for target in targets:
            if target in added_targets:
                handler = LoggingUtils.create_logging_handler(target, logger.tango_logger)
                logger.addHandler(handler)

        logger.info('Logging targets set to %s', targets)


# PROTECTED REGION END #    //  SKABaseDevice.additionnal_import


__all__ = ["SKABaseDevice", "main"]


class SKABaseDevice(Device):
    """
    A generic base device for SKA.

    Advice for subclassers:

    * This device implements the SKA control model so that you don't
      have to. Instead of subclassing commands and `init_device`
      directly, you are highly recommended to subclass the stateless
      hooks commencing with `do_`; for example, `do_init_device`,
      `do_Scan`, etc.
    * You `do_` hooks must return a `(return_code, message)` tuple, e.g.
      `return (ReturnCode.OK, "Scan command executed")
    * Synchronous `do_` hooks must return a return code of OK or FAILED.
      This will ensure that state is updated upon completion.
    * Asynchronous `do_` hooks must return a return code of STARTED or
      QUEUED; and it is your responsibility to ensure that your
      asynchronous work finishes by calling `[Command]_completed` with a
      return code of OK or FAILED.
    * If your `do_` hooks raises an uncaught exception, the device will
      be put into state FAULT.
    * If you must modify the handling of device, you may do so by
      subclassing the `[Command]_requested` and `[Command]_completed`
      methods.
    """
    # PROTECTED REGION ID(SKABaseDevice.class_variable) ENABLED START #
    guard.register(
        "state",
        lambda device, state: device.get_state() == state
    )
    guard.register(
        "states",
        lambda device, states: device.get_state() in states
    )
    guard.register(
        "admin_modes",
        lambda device, admin_modes: device._admin_mode in admin_modes
    )

    _logging_config_lock = threading.Lock()
    _logging_configured = False

    def _init_logging(self):
        """
        This method initializes the logging mechanism, based on default properties.
        """

        class EnsureTagsFilter(logging.Filter):
            """Ensure all records have a "tags" field - empty string, if not provided."""
            def filter(self, record):
                if not hasattr(record, "tags"):
                    record.tags = ""
                return True

        # There may be multiple devices in a single device server - these will all be
        # starting at the same time, so use a lock to prevent race conditions, and
        # a flag to ensure the SKA standard logging configuration is only applied once.
        with SKABaseDevice._logging_config_lock:
            if not SKABaseDevice._logging_configured:
                ska_logging.configure_logging(tags_filter=EnsureTagsFilter)
                SKABaseDevice._logging_configured = True

        device_name = self.get_name()
        self.logger = logging.getLogger(device_name)
        # device may be reinitialised, so remove existing handlers and filters
        for handler in list(self.logger.handlers):
            self.logger.removeHandler(handler)
        for filt in list(self.logger.filters):
            self.logger.removeFilter(filt)

        # add a filter with this device's name
        device_name_tag = "tango-device:{}".format(device_name)

        class TangoDeviceTagsFilter(logging.Filter):
            def filter(self, record):
                record.tags = device_name_tag
                return True

        self.logger.addFilter(TangoDeviceTagsFilter())

        # before setting targets, give Python logger a reference to the log4tango logger
        # to support the TangoLoggingServiceHandler target option
        self.logger.tango_logger = self.get_logger()

        # initialise using defaults in device properties
        self._logging_level = None
        self.write_loggingLevel(self.LoggingLevelDefault)
        self.write_loggingTargets(self.LoggingTargetsDefault)
        self.logger.debug('Logger initialised')

        # monkey patch TANGO Logging Service streams so they go to the Python
        # logger instead
        self.debug_stream = self.logger.debug
        self.info_stream = self.logger.info
        self.warn_stream = self.logger.warning
        self.error_stream = self.logger.error
        self.fatal_stream = self.logger.critical

    # PROTECTED REGION END #    //  SKABaseDevice.class_variable

    # -----------------
    # Device Properties
    # -----------------

    SkaLevel = device_property(
        dtype='int16', default_value=4
    )

    GroupDefinitions = device_property(
        dtype=('str',),
    )

    LoggingLevelDefault = device_property(
        dtype='uint16', default_value=LoggingLevel.INFO
    )

    LoggingTargetsDefault = device_property(
        dtype='DevVarStringArray', default_value=["tango::logger"]
    )

    # ----------
    # Attributes
    # ----------

    buildState = attribute(
        dtype='str',
        doc="Build state of this device",
    )

    versionId = attribute(
        dtype='str',
        doc="Version Id of this device",
    )

    loggingLevel = attribute(
        dtype=LoggingLevel,
        access=AttrWriteType.READ_WRITE,
        doc="Current logging level for this device - "
            "initialises to LoggingLevelDefault on startup",
    )

    loggingTargets = attribute(
        dtype=('str',),
        access=AttrWriteType.READ_WRITE,
        max_dim_x=4,
        doc="Logging targets for this device, excluding ska_logging defaults"
            " - initialises to LoggingTargetsDefault on startup",
    )

    healthState = attribute(
        dtype=HealthState,
        doc="The health state reported for this device. "
            "It interprets the current device"
            " condition and condition of all managed devices to set this. "
            "Most possibly an aggregate attribute.",
    )

    adminMode = attribute(
        dtype=AdminMode,
        access=AttrWriteType.READ_WRITE,
        memorized=True,
        doc="The admin mode reported for this device. It may interpret the current "
            "device condition and condition of all managed devices to set this. "
            "Most possibly an aggregate attribute.",
    )

    controlMode = attribute(
        dtype=ControlMode,
        access=AttrWriteType.READ_WRITE,
        memorized=True,
        doc="The control mode of the device. REMOTE, LOCAL"
            "\nTANGO Device accepts only from a ‘local’ client and ignores commands and "
            "queries received from TM or any other ‘remote’ clients. The Local clients"
            " has to release LOCAL control before REMOTE clients can take control again.",
    )

    simulationMode = attribute(
        dtype=SimulationMode,
        access=AttrWriteType.READ_WRITE,
        memorized=True,
        doc="Reports the simulation mode of the device. \nSome devices may implement "
            "both modes, while others will have simulators that set simulationMode "
            "to True while the real devices always set simulationMode to False.",
    )

    testMode = attribute(
        dtype=TestMode,
        access=AttrWriteType.READ_WRITE,
        memorized=True,
        doc="The test mode of the device. \n"
            "Either no test mode or an "
            "indication of the test mode.",
    )

    # ---------------
    # General methods
    # ---------------

    def _call_with_pattern(self, argin=None):
        """
        Implements the common calling pattern for all commands.

        :param argin: the argument provided to the Command, if any
        :type argin: any tango argument type
        :return: a ResultCode and descriptive message
        :rtype: tango.DevVarLongStringArray
        """
        command_name = inspect.currentframe().f_back.f_code.co_name
        requested_name = "{}_requested".format(command_name)
        do_name = "do_{}".format(command_name)
        completed_name = "{}_completed".format(command_name)

        command_requested = getattr(self, requested_name, None)
        do_command = getattr(self, do_name, None)
        command_completed = getattr(self, completed_name, None)

        try:
            if command_requested is not None:
                command_requested()  # pylint: disable=not-callable

            if argin is None:
                (return_code, message) = do_command()  # pylint: disable=not-callable
            else:
                (return_code, message) = do_command(argin)  # pylint: disable=not-callable

            if return_code in [ReturnCode.OK, ReturnCode.FAILED]:
                command_completed(return_code)  # pylint: disable=not-callable
        except Exception:
            self.set_state(DevState.FAULT)
            self.set_status("The device is in FAULT state.")
            raise

        self.logger.info(
            "Exiting {} with return code {}, message '{}'".format(
                command_name,
                return_code,
                message
            )
        )
        return (return_code, message)

    def init_device(self):
        """
        Method that initializes the tango device after startup.

        :return: None
        """
        super().init_device()
        try:
            self._call_with_pattern()
        except Exception:
            self.set_state(DevState.FAULT)
            self.set_status("The device is in FAULT state")

    def init_device_requested(self):
        """
        Method that manages device state in response to `init_device`
        being invoked.
        """
        self.set_state(DevState.INIT)
        self.set_status("The device is in INIT state.")

        # The "factory default" for AdminMode is MAINTENANCE. But fear
        # not, it is a memorized attribute and will soon be overwritten
        # with its memorized value.
        self._admin_mode = AdminMode.MAINTENANCE

    def do_init_device(self):
        """
        Stateless hook for initialisation of device attributes and other
        internal values. Subclasses that have no need to override the
        default implementation of state management may leave
        ``init_device`` alone and override this method instead.

        :return: A tuple containing a return code and a string message
            indicating status. The message is for information purpose
            only.
        :rtype: (ReturnCode, str)
        """
        self._health_state = HealthState.OK
        self._control_mode = ControlMode.REMOTE
        self._simulation_mode = SimulationMode.FALSE
        self._test_mode = TestMode.NONE

        self._build_state = '{}, {}, {}'.format(release.name, release.version,
                                                release.description)
        self._version_id = release.version

        self._init_logging()
        try:
            # create TANGO Groups objects dict, according to property
            self.logger.debug("Groups definitions: {}".format(self.GroupDefinitions))
            self.groups = get_groups_from_json(self.GroupDefinitions)
            self.logger.info("Groups loaded: {}".format(sorted(self.groups.keys())))
        except GroupDefinitionsError:
            self.logger.info("No Groups loaded for device: {}".format(self.get_name()))

        return (ReturnCode.OK, "init_device executed")

    @guard(state=DevState.INIT)
    def init_device_completed(self, return_code):
        """
        Updates device state on completion of initialisation.
        """
        if self._admin_mode in [AdminMode.ONLINE, AdminMode.MAINTENANCE]:
            self.set_state(DevState.OFF)
            self.set_status("The device is in OFF state.")
        else:  # admin_mode is in [AdminMode.OFFLINE, AdminMode.NOT_FITTED]
            self.set_state(DevState.DISABLE)
            self.set_status("The device is in DISABLE state.")

    def always_executed_hook(self):
        # PROTECTED REGION ID(SKABaseDevice.always_executed_hook) ENABLED START #
        """
        Method that is always executed before any device command gets executed.

        :return: None
        """
        # PROTECTED REGION END #    //  SKABaseDevice.always_executed_hook

    def delete_device(self):
        # PROTECTED REGION ID(SKABaseDevice.delete_device) ENABLED START #
        """
        Method to cleanup when device is stopped.

        :return: None
        """
        # PROTECTED REGION END #    //  SKABaseDevice.delete_device

    # ------------------
    # Attributes methods
    # ------------------

    def read_buildState(self):
        # PROTECTED REGION ID(SKABaseDevice.buildState_read) ENABLED START #
        """
        Reads the Build State of the device.

        :return: None
        """
        return self._build_state
        # PROTECTED REGION END #    //  SKABaseDevice.buildState_read

    def read_versionId(self):
        # PROTECTED REGION ID(SKABaseDevice.versionId_read) ENABLED START #
        """
        Reads the Version Id of the device.

        :return: None
        """
        return self._version_id
        # PROTECTED REGION END #    //  SKABaseDevice.versionId_read

    def read_loggingLevel(self):
        # PROTECTED REGION ID(SKABaseDevice.loggingLevel_read) ENABLED START #
        """
        Reads logging level of the device.

        :return:  Logging level of the device.
        """
        return self._logging_level
        # PROTECTED REGION END #    //  SKABaseDevice.loggingLevel_read

    def write_loggingLevel(self, value):
        # PROTECTED REGION ID(SKABaseDevice.loggingLevel_write) ENABLED START #
        """
        Sets logging level for the device.  Both the Python logger and the
        Tango logger are updated.

        :param value: Logging level for logger

        :return: None.
        """
        try:
            lmc_logging_level = LoggingLevel(value)
        except ValueError:
            raise LoggingLevelError(
                "Invalid level - {} - must be one of {} ".format(
                    value, [v for v in LoggingLevel.__members__.values()]))

        self._logging_level = lmc_logging_level
        self.logger.setLevel(_LMC_TO_PYTHON_LOGGING_LEVEL[lmc_logging_level])
        self.logger.tango_logger.set_level(_LMC_TO_TANGO_LOGGING_LEVEL[lmc_logging_level])
        self.logger.info('Logging level set to %s on Python and Tango loggers', lmc_logging_level)
        # PROTECTED REGION END #    //  SKABaseDevice.loggingLevel_write

    def read_loggingTargets(self):
        # PROTECTED REGION ID(SKABaseDevice.loggingTargets_read) ENABLED START #
        """
        Reads the additional logging targets of the device.

        Note that this excludes the handlers provided by the ska_logging
        library defaults.

        :return:  Logging level of the device.
        """
        return [str(handler.name) for handler in self.logger.handlers]
        # PROTECTED REGION END #    //  SKABaseDevice.loggingTargets_read

    def write_loggingTargets(self, value):
        # PROTECTED REGION ID(SKABaseDevice.loggingTargets_write) ENABLED START #
        """
        Sets the additional logging targets for the device.

        Note that this excludes the handlers provided by the ska_logging
        library defaults.

        :param value: Logging targets for logger

        :return: None.
        """
        device_name = self.get_name()
        valid_targets = LoggingUtils.sanitise_logging_targets(value, device_name)
        LoggingUtils.update_logging_handlers(valid_targets, self.logger)
        # PROTECTED REGION END #    //  SKABaseDevice.loggingTargets_write

    def read_healthState(self):
        # PROTECTED REGION ID(SKABaseDevice.healthState_read) ENABLED START #
        """
        Reads Health State of the device.

        :return: Health State of the device
        """
        return self._health_state
        # PROTECTED REGION END #    //  SKABaseDevice.healthState_read

    def read_adminMode(self):
        # PROTECTED REGION ID(SKABaseDevice.adminMode_read) ENABLED START #
        """
        Reads Admin Mode of the device.

        :return: Admin Mode of the device
        """
        return self._admin_mode
        # PROTECTED REGION END #    //  SKABaseDevice.adminMode_read

    def write_adminMode(self, value):
        # PROTECTED REGION ID(SKABaseDevice.adminMode_write) ENABLED START #
        """
        Sets Admin Mode of the device.

        :param value: Admin Mode of the device.

        :return: None
        """
        enabling_modes = [AdminMode.ONLINE, AdminMode.MAINTENANCE]
        disabling_modes = [AdminMode.OFFLINE, AdminMode.NOT_FITTED]

        state = self.get_state()
        if state == DevState.DISABLE and value in enabling_modes:
            # This write enables the subarray
            self.set_state(DevState.OFF)
            self.set_status("The device is in OFF state.")
        elif state in [DevState.OFF, DevState.ON] and value in disabling_modes:
            self.set_state(DevState.DISABLE)
            self.set_status("The device is in DISABLE state.")
        self._admin_mode = value
        # PROTECTED REGION END #    //  SKABaseDevice.adminMode_write

    def read_controlMode(self):
        # PROTECTED REGION ID(SKABaseDevice.controlMode_read) ENABLED START #
        """
        Reads Control Mode of the device.

        :return: Control Mode of the device
        """
        return self._control_mode
        # PROTECTED REGION END #    //  SKABaseDevice.controlMode_read

    def write_controlMode(self, value):
        # PROTECTED REGION ID(SKABaseDevice.controlMode_write) ENABLED START #
        """
        Sets Control Mode of the device.

        :param value: Control mode value

        :return: None
        """
        self._control_mode = value
        # PROTECTED REGION END #    //  SKABaseDevice.controlMode_write

    def read_simulationMode(self):
        # PROTECTED REGION ID(SKABaseDevice.simulationMode_read) ENABLED START #
        """
        Reads Simulation Mode of the device.

        :return: Simulation Mode of the device.
        """
        return self._simulation_mode
        # PROTECTED REGION END #    //  SKABaseDevice.simulationMode_read

    def write_simulationMode(self, value):
        # PROTECTED REGION ID(SKABaseDevice.simulationMode_write) ENABLED START #
        """
        Sets Simulation Mode of the device

        :param value: SimulationMode

        :return: None
        """
        self._simulation_mode = value
        # PROTECTED REGION END #    //  SKABaseDevice.simulationMode_write

    def read_testMode(self):
        # PROTECTED REGION ID(SKABaseDevice.testMode_read) ENABLED START #
        """
        Reads Test Mode of the device.

        :return: Test Mode of the device
        """
        return self._test_mode
        # PROTECTED REGION END #    //  SKABaseDevice.testMode_read

    def write_testMode(self, value):
        # PROTECTED REGION ID(SKABaseDevice.testMode_write) ENABLED START #
        """
        Sets Test Mode of the device.

        :param value: Test Mode

        :return: None
        """
        self._test_mode = value
        # PROTECTED REGION END #    //  SKABaseDevice.testMode_write

    # --------
    # Commands
    # --------

    @command(dtype_out=('str',), doc_out="Version strings",)
    @DebugIt()
    def GetVersionInfo(self):
        # PROTECTED REGION ID(SKABaseDevice.GetVersionInfo) ENABLED START #
        """
        Returns the version information of the device.

        :return: Version details of the device.
        """
        return ['{}, {}'.format(self.__class__.__name__, self.read_buildState())]
        # PROTECTED REGION END #    //  SKABaseDevice.GetVersionInfo

    @command(
    )
    @DebugIt()
    def Reset(self):
        """
        Command to reset the device to its default state.
        """
        self._call_with_pattern()

    def Reset_requested(self):
        """
        Method that manages device state in response to `Reset` command
        being invoked.
        """
        pass

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
        return (ReturnCode.OK, "Device reset")

    def Reset_completed(self, return_code):
        """
        Method that manages device state in response to completion of
        the `Reset` command.
        """
        self._health_state = HealthState.OK
        self._control_mode = ControlMode.REMOTE
        self._simulation_mode = SimulationMode.FALSE
        self._test_mode = TestMode.NONE

        if self._admin_mode in [AdminMode.ONLINE, AdminMode.MAINTENANCE]:
            self.set_state(DevState.OFF)
            self.set_status("The device is in OFF state.")

        else:  # admin_mode is in [AdminMode.OFFLINE, AdminMode.NOT_FITTED]
            self.set_state(DevState.DISABLE)
            self.set_status("The device is in DISABLE state.")

# ----------
# Run server
# ----------


def main(args=None, **kwargs):
    # PROTECTED REGION ID(SKABaseDevice.main) ENABLED START #
    """
    Main function of the SKABaseDevice module.

    :param args: None

    :param kwargs:

    :return:
    """
    return run((SKABaseDevice,), args=args, **kwargs)
    # PROTECTED REGION END #    //  SKABaseDevice.main


if __name__ == '__main__':
    main()
