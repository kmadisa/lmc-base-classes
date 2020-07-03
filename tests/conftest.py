"""
A module defining a list of fixtures that are shared across all ska.base tests.
"""
import importlib
import pytest
import time

from tango import EventType
from tango.test_context import DeviceTestContext

from ska.base import SKASubarrayStateModel


@pytest.fixture(scope="class")
def tango_context(request):
    """Creates and returns a TANGO DeviceTestContext object.

    Parameters
    ----------
    request: _pytest.fixtures.SubRequest
        A request object gives access to the requesting test context.
    """
    test_properties = {
        'SKAMaster': {
            'SkaLevel': '4',
            'LoggingTargetsDefault': '',
            'GroupDefinitions': '',
            'NrSubarrays': '16',
            'CapabilityTypes': '',
            'MaxCapabilities': ['BAND1:1', 'BAND2:1']
            },

        'SKASubarray': {
            "CapabilityTypes": ["BAND1", "BAND2"],
            'LoggingTargetsDefault': '',
            'GroupDefinitions': '',
            'SkaLevel': '4',
            'SubID': '1',
        },
    }

    # This fixture is used to decorate classes like "TestSKABaseDevice" or
    # "TestSKALogger". We drop the first "Test" from the string to get the
    # class name of the device under test.
    # Similarly, the test module is like "test_base_device.py".  We drop the
    # first "test_" to get the module name
    test_class_name = request.cls.__name__
    class_name = test_class_name.split('Test', 1)[-1]
    module = importlib.import_module("ska.base", class_name)
    class_type = getattr(module, class_name)

    tango_context = DeviceTestContext(class_type, properties=test_properties.get(class_name))
    tango_context.start()
    yield tango_context
    tango_context.stop()


@pytest.fixture(scope="function")
def initialize_device(tango_context):
    """Re-initializes the device.

    Parameters
    ----------
    tango_context: tango.test_context.DeviceTestContext
        Context to run a device without a database.
    """
    yield tango_context.device.Init()


@pytest.fixture(scope="function")
def state_model():
    """
    Yields an SKASubarrayStateModel.
    """
    yield SKASubarrayStateModel()


@pytest.fixture(scope="function")
def tango_change_event_helper(tango_context):
    """
    Helper for testing tango change events. To use it, call the subscribe
    method with the name of the attribute for which you want change events.
    The returned value will be a callback handler that you can interrogate
    with ``called`` and ``expect_call_with`` methods.::

    .. code-block:: python

        state_callback = tango_change_event_helper.subscribe("State")
        assert state_callback.expect_call_with(DevState.OFF)

        # Check that we can't turn off a device that isn't on
        with pytest.raises(DevFailed):
            tango_context.device.Off()
        assert not state_callback.called()

        # Now turn it on and check that we can turn it off
        tango_context.device.On()
        assert state_callback.expect_call_with(DevState.ON)

    """
    class _Callback:
        @staticmethod
        def subscribe(attribute_name):
            return _Callback(attribute_name)

        def __init__(self, attribute_name):
            self._called = False
            self._value = None

            self._id = tango_context.device.subscribe_event(
                attribute_name, EventType.CHANGE_EVENT, self
            )

        def __del__(self):
            tango_context.device.unsubscribe_event(self._id)

        def __call__(self, event_data):
            self._value = event_data.attr_value.value
            self._called = True

        def called(self):
            retries = 60
            for _ in range(retries):
                if self._called:
                    break
                time.sleep(0.05)
            return self._called

        @property
        def value(self):
            if self.called():
                self._called = False
            return self._value

        def expect_call_with(self, value):
            if not self.called():
                return None
            self._called = False
            return self._value == value

    yield _Callback
