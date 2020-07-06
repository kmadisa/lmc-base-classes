"""
A module defining a list of fixtures that are shared across all ska.base tests.
"""
import importlib
import pytest
from queue import Empty, Queue

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
    with ``called``, ``expect_call_with``, ``expect_calls_with``,
    ``value``, or ``values`` methods.  This interrogation must only be done
    using a single call to **one** of those methods per expected event(s).::

    .. code-block:: python

        state_callback = tango_change_event_helper.subscribe("state")
        assert state_callback.expect_call_with(DevState.OFF)

        # Check that we can't turn off a device that isn't on
        with pytest.raises(DevFailed):
            tango_context.device.Off()
        assert not state_callback.called()

        # Now turn it on and check that we can turn it off
        tango_context.device.On()
        assert state_callback.expect_call_with(DevState.ON)

        # Or we can test a sequence of events
        tango_context.device.Off()
        tango_context.device.On()
        assert state_callback.expect_calls_with([DevState.OFF, DevState.ON])

    """
    class _Callback:
        @staticmethod
        def subscribe(attribute_name):
            return _Callback(attribute_name)

        def __init__(self, attribute_name):
            self._value = None
            self._values_queue = Queue()
            self._errors = []

            # Subscription will result in an immediate
            # synchronous callback with the current value,
            # so keep this as the last step in __init__.
            self._id = tango_context.device.subscribe_event(
                attribute_name, EventType.CHANGE_EVENT, self
            )

        def __del__(self):
            if hasattr(self, "_id"):
                tango_context.device.unsubscribe_event(self._id)

        def __call__(self, event_data):
            if event_data.err:
                error = event_data.errors[0]
                self._errors.append("Event callback error: [%s] %s" % (error.reason, error.desc))
            else:
                self._values_queue.put(event_data.attr_value.value)

        def _next(self):
            assert not self._errors, f"Some errors: {self._errors}"
            try:
                return self._values_queue.get(timeout=1.5)
            except Empty:
                return None

        @property
        def value(self):
            new_value = self._next()
            while new_value is not None:
                self._value = new_value
                new_value = self._next()
            return self._value

        def assert_not_called(self):
            assert not self._values_queue.qsize()

        def assert_call(self, value):
            assert self._next() == value

        def assert_calls(self, values):
            for value in values:
                self.assert_call(value)

    yield _Callback
