"""
A module defining a list of fixtures that are shared across all ska.base tests.
"""
import importlib
import itertools
import pytest
from queue import Empty, Queue
from transitions import MachineError

from tango import EventType
from tango.test_context import DeviceTestContext

from ska.base import SKABaseDeviceStateModel, SKASubarrayStateModel


def pytest_configure(config):
    """
    pytest hook, used here to register custom marks to get rid of spurious
    warnings
    """
    config.addinivalue_line(
        "markers",
        "state_machine_test: indicate that the test is a state machine "
        "test and should be parameterised by the states and actions in "
        "its DAG"
    )


def pytest_generate_tests(metafunc):
    """
    pytest hook that generates tests; this hook ensures that any test
    that is marked with `state_machine_test` custom marker will be
    parameterised by the states and actions in its DAG
    """
    # called once per each test function
    if metafunc.definition.get_closest_marker("state_machine_test"):
        metafunc.parametrize(*metafunc.cls._parametrize())


@pytest.mark.state_machine_test
class StateMachineTester:
    """
    Abstract base class for a class for testing state machines
    """

    @classmethod
    def _parametrize(cls):
        """
        Parametrizes the state machine tests to ensure that every action
        in the DAG is tested from every state in the DAG.
        """
        states = set()
        triggers = set()
        expected = {}

        for (from_state, trigger, to_state) in cls.dag:
            states.add(from_state)
            states.add(to_state)
            triggers.add(trigger)
            expected[(from_state, trigger)] = to_state

        states = sorted(states)
        triggers = sorted(triggers)

        return (
            "state_under_test, action_under_test, expected_state",
            [
                (
                    state,
                    trigger,
                    expected[(state, trigger)] if (state, trigger) in expected else None
                ) for (state, trigger) in itertools.product(states, triggers)
            ]
        )

    def test_state_machine(
        self, state_under_test, action_under_test, expected_state,
    ):
        """
        Test the subarray state machine: for a given initial state and
        an action, does execution of that action, from that initial
        state, yield the expected results? If the action was not allowed
        from that initial state, does the device raise a DevFailed
        exception? If the action was allowed, does it result in the
        correct state transition?

        :todo: support starting in different memorised adminModes
        """
        # Put the device into the state under test
        self.to_state(state_under_test)

        # Check that we are in the state under test
        self.assert_state(state_under_test)

        # Test that the action under test does what we expect it to
        if expected_state is None:
            # Action should fail and the state should not change
            self.assert_fails(action_under_test)
            self.assert_state(state_under_test)
        else:
            # Action should succeed
            self.perform_action(action_under_test)
            self.assert_state(expected_state)

    def assert_state(self, state):
        """
        Abstract method for asserting the current state of the state
        machine under test

        :param state: the state that we are asserting to be the current
            state of the state machine under test
        :type state: str
        """
        raise NotImplementedError()

    def perform_action(self, action):
        """
        Abstract method for performing a triggering action on the state
        machine

        :param action: action to be performed on the state machine
        :type action: str
        """
        raise NotImplementedError()

    def assert_fails(self, action):
        """
        Abstract method for asserting that an action fails if performed
        on the state machine under test in its current state.

        :param action: action to be performed on the state machine
        :type action: str
        """
        raise NotImplementedError()

    def to_state(self, target_state):
        """
        Abstract method for getting the state machine into a target
        state.

        :param target_state: the state that we want to get the state
            machine under test into
        :type target_state: str
        """
        raise NotImplementedError()


class TransitionsStateMachineTester(StateMachineTester):
    """
    Much less abstract implementation of a StateMachineTester for a
    pytransitions state machine. Requires only implementation of the
    `machine` property for obtaining the machine. Assumes that the DAG
    states and actions are the states and triggers of the pytransitions
    machine.
    """

    @property
    def machine(self):
        """
        Returns a pytransitions Machine for testing that it implements
        the state diagram described by the DAG
        """
        raise NotImplementedError()

    def assert_state(self, state):
        """
        Assert the current state of the state machine under test.

        :param state: the state that we are asserting to be the current
            state of the state machine under test
        :type state: str
        """
        assert self.machine.state == state

    def perform_action(self, action):
        """
        Perform a given action on the state machine under test.

        :param action: action to be performed on the state machine
        :type action: str
        """
        self.machine.trigger(action)

    def assert_fails(self, action):
        """
        Assert that performing a given action on the state maching under
        test fails in its current state.

        :param action: action to be performed on the state machine
        :type action: str
        """
        with pytest.raises(MachineError):
            self.perform_action(action)

    def to_state(self, target_state):
        """
        Transition the state machine to a target state.

        :param target_state: the state that we want to get the state
            machine under test into
        :type target_state: str
        """
        self.machine.trigger(f"to_{target_state}")


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


@pytest.fixture
def device_state_model():
    """
    Yields a new SKABaseDeviceStateModel for testing
    """
    yield SKABaseDeviceStateModel()


@pytest.fixture
def subarray_state_model():
    """
    Yields a new SKASubarrayStateModel for testing
    """
    yield SKASubarrayStateModel()


@pytest.fixture(scope="function")
def tango_change_event_helper(tango_context):
    """
    Helper for testing tango change events. To use it, call the subscribe
    method with the name of the attribute for which you want change events.
    The returned value will be a callback handler that you can interrogate
    with ``assert_not_called``, ``assert_call``, ``assert_calls``, and
    ``value`` methods.::

    .. code-block:: python

        state_callback = tango_change_event_helper.subscribe("state")
        state_callback.assert_call(DevState.OFF)

        # Check that we can't turn off a device that isn't on
        with pytest.raises(DevFailed):
            tango_context.device.Off()
        state_callback.assert_not_called()

        # Now turn it on and check that we can turn it off
        tango_context.device.On()
        state_callback.assert_call(DevState.ON)

        # Or we can test a sequence of events
        tango_context.device.Off()
        tango_context.device.On()
        state_callback.assert_calls([DevState.OFF, DevState.ON])

    """
    class _Callback:
        """
        Private callback handler class, an instance of which is returned
        by the tango_change_event_helper each time it is used to
        subscribe to a change event.
        """
        @staticmethod
        def subscribe(attribute_name):
            """
            Returns an event subscriber helper object that is subscribed
            to change events on the named attribute.

            :param attribute_name: name of the attribute for which
                change events will be subscribed
            :type attribute_name: str
            :return: an event subscriber helper object
            :rtype: object
            """
            return _Callback(attribute_name)

        def __init__(self, attribute_name):
            """
            Creates an event subscriber helper object that is subscribed
            to change events on the name attribute

            :param attribute_name: name of the attribute for which
                change events will be subscribed
            :type attribute_name: str
            """
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
            """
            Unsubscribe from events before object is destroyed
            """
            if hasattr(self, "_id"):
                tango_context.device.unsubscribe_event(self._id)

        def __call__(self, event_data):
            """
            Event subscription callback

            :param event_data: data about the change events
            :type event_data: tango.EventData
            """
            if event_data.err:
                error = event_data.errors[0]
                self._errors.append("Event callback error: [%s] %s" % (error.reason, error.desc))
            else:
                self._values_queue.put(event_data.attr_value.value)

        def _next(self):
            """
            Gets the attribute value from the next event if there is
            one or if it arrives in time.

            :return: the attribute value reported in next change event,
                or None if there is no event
            :rtype: same as attribute type
            """
            assert not self._errors, f"Some errors: {self._errors}"
            try:
                return self._values_queue.get(timeout=1.5)
            except Empty:
                return None

        def assert_not_called(self):
            """
            Assert that there are no new callbacks calls. (That is,
            there are no callback calls that have not already been
            consumed by an ``assert_call`` or ``assert_calls``.)
            """
            assert self._values_queue.empty()

        def assert_call(self, value):
            """
            Asserts that this callback has been called with a change
            event that updates the attribute value to a given value.

            Note that this method consumes a single event, but may leave
            other events unconsumed.

            :param value: the value that the attribute is asserted to
                have been changed to
            :type value: same as the attribute type
            """
            assert self._next() == value

        def assert_calls(self, values):
            """
            Asserts that this callback has been called with a sequence
            of change events that update the attribute values to the
            given sequence of values.

            Note that this method consumes the events associated with
            the given values, but may leave subsequent events
            unconsumed.

            :param values: sequence of values that the attribute
                is asserted to have been changed to
            :type values: list
            """
            for value in values:
                self.assert_call(value)

    yield _Callback
