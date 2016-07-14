import inspect

from pacman.executor.single_input import SingleInput
from pacman import exceptions

from spinn_machine.utilities.ordered_set import OrderedSet
from pacman.executor.all_of_input import AllOfInput
from pacman.executor.one_of_input import OneOfInput
from pacman.executor.python_class_algorithm import PythonClassAlgorithm

_algorithms = list()


class AllOf(object):

    __slots__ = ["_items"]

    def __init__(self, *items):
        self._items = items

    @property
    def items(self):
        return self._items

    @property
    def real_class(self):
        return AllOfInput


class OneOf(object):

    __slots__ = ["_items"]

    def __init__(self, *items):
        self._items = items

    @property
    def items(self):
        return self._items

    @property
    def real_class(self):
        return OneOfInput


def _decode_inputs(input_defs, inputs):
    final_inputs = list()
    for inp in inputs:
        if isinstance(inp, str):
            if inp not in input_defs:
                raise exceptions.PacmanConfigurationException(
                    "Input {} not found in input_definitions".format(inp))
            final_inputs.append(input_defs[inp])
        else:
            final_inputs.append(inp.real_class(
                _decode_inputs(input_defs, inp.items)))

    return final_inputs


def _decode_algorithm_details(
        input_definitions, required_inputs, optional_inputs,
        file_inputs, function, has_self=False):
    function_args = inspect.getargspec(function)
    required_args = OrderedSet(
        function_args.args[:-len(function_args.defaults)])
    optional_args = OrderedSet(
        function_args.args[-len(function_args.defaults):])

    # Parse the input definitions
    input_defs = dict()
    for (input_name, input_types) in input_definitions.iteritems():
        if (input_name not in required_args and
                input_name not in optional_args):
            raise exceptions.PacmanConfigurationException(
                "Algorithm {} has no parameter named {} but found one"
                " in the input_definitions".format(
                    algorithm_class, input_name))
        is_file = False
        if file_inputs is not None:
            is_file = input_name in file_inputs
        input_defs[input_name] = SingleInput(
            input_name, list(input_types), is_file)

    # Check that there is a definition for every argument
    for arg in function_args.args:
        if arg not in input_defs and (not has_self or arg != "self"):
            raise exceptions.PacmanConfigurationException(
                "Algorithm {} has no input_definition for the"
                " parameter {}".format(
                    algorithm_class, arg))

    # Get the required arguments
    final_required_inputs = None
    if required_inputs is None:
        final_required_inputs = [
            input_defs[arg] for arg in required_args
            if (not has_self or arg != "self")
        ]
    else:
        final_required_inputs = _decode_inputs(input_defs, required_inputs)

    # Get the optional arguments
    final_optional_inputs = None
    if optional_inputs is None:
        final_optional_inputs = [
            input_defs[arg] for arg in optional_args
            if (not has_self or arg != "self")
        ]
    else:
        final_optional_inputs = _decode_inputs(input_defs, optional_inputs)

    return final_required_inputs, final_optional_inputs


def algorithm_class(
        input_definitions, outputs, algorithm_id=None, required_inputs=None,
        optional_inputs=None, method=None, file_inputs=None):

    def wrap(algorithm_class):

        # Get the algorithm id
        final_algorithm_id = algorithm_id
        if algorithm_id is None:
            final_algorithm_id = algorithm_class.__name__

        # Get the details of the method
        method_to_call = method
        if method is None:
            method_to_call = "__call__"
        actual_method = getattr(algorithm_class, method_to_call)

        # Get the inputs
        final_required_inputs, final_optional_inputs = \
            _decode_algorithm_details(
                input_definitions, required_inputs, optional_inputs,
                file_inputs, actual_method, has_self=True)

        # Add the algorithm
        _algorithms.append(PythonClassAlgorithm(
            final_algorithm_id, final_required_inputs, final_optional_inputs,
            outputs, algorithm_class.__module__, algorithm_class,
            method_to_call))

        return algorithm_class
    return wrap


@algorithm_class(
    input_definitions={
        "chocolate": "MemoryChocolate",
        "whisky": "MemoryWhisky",
        "dave": "MemoryDave",
        "bacon": ["MemoryBacon", "MemoryBurnedBacon"]
    },
    outputs=["MemoryPlates", "MemoryCups"])
class Lunch(object):

    def __call__(self, chocolate, whisky=None, dave=None, bacon=None):
        return "Plates", "Cups"

print _algorithms
