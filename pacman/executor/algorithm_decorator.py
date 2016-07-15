import inspect
import pkgutil
import os
import importlib

from spinn_machine.utilities.ordered_set import OrderedSet

from pacman.executor.single_input import SingleInput
from pacman import exceptions
from pacman.executor.all_of_input import AllOfInput
from pacman.executor.one_of_input import OneOfInput
from pacman.executor.python_class_algorithm import PythonClassAlgorithm
from pacman.executor.python_function_algorithm import PythonFunctionAlgorithm

# The list of algorithms found
_algorithms = list()


class AllOf(object):
    """ Indicates that all of the items specified are required
    """

    __slots__ = ["_items"]

    def __init__(self, *items):
        """
        :param items: The items required
        :type items: str, AllOf, OneOf
        """
        self._items = items

    @property
    def items(self):
        """ The items specified
        """
        return self._items

    @property
    def real_class(self):
        """ The AbstractInput class to use for this input
        """
        return AllOfInput


class OneOf(object):
    """ Indicates that one of the items specified is required
    """

    __slots__ = ["_items"]

    def __init__(self, *items):
        """
        :param items: The items required
        :type items: str, AllOf, OneOf
        """
        self._items = items

    @property
    def items(self):
        """ The items specified
        """
        return self._items

    @property
    def real_class(self):
        """ The AbstractInput class to use for this input
        """
        return OneOfInput


def _decode_inputs(input_defs, inputs):
    """ Converts the inputs specified to actual input classes

    :param input_defs: A dict of algorithm parameter name SingleInput
    :param inputs: A list of inputs to decode
    :type inputs: list of str, OneOf, AllOf
    :return: a list of AbstractInput
    """
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
    """ Convert the algorithm annotation inputs to input classes

    :param input_definitions: dict of algorithm parameter name to list of types
    :param required_inputs: List of required algorithm parameter names
    :type required_inputs: list of str, OneOf, AllOf
    :param optional_inputs: List of optional algorithm parameter names
    :type optional_inputs: list of str, OneOf, AllOf
    :param file_inputs: set of algorithm parameter names that are files
    :param function: The function to be called by the algorithm
    :param has_self: True if the self parameter is expected
    """
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
                "No parameter named {} but found one"
                " in the input_definitions".format(input_name))
        is_file = False
        if file_inputs is not None:
            is_file = input_name in file_inputs
        if not isinstance(input_types, list):
            input_types = [input_types]
        input_defs[input_name] = SingleInput(
            input_name, input_types, is_file)

    # Check that there is a definition for every argument
    for arg in function_args.args:
        if arg not in input_defs and (not has_self or arg != "self"):
            raise exceptions.PacmanConfigurationException(
                "No input_definition for the argument {}".format(arg))

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


def algorithm(
        input_definitions, outputs, algorithm_id=None, required_inputs=None,
        optional_inputs=None, method=None, file_inputs=None):
    """ Define an object to be a PACMAN algorithm that can be executed by\
        the PacmanAlgorithmExecutor.

        Can be used to decorate either a class or a function (not a method).\
        If this decorates a class, the class must be callable (i.e. have a\
        __call__ method), or else a method must be specified to call to run\
        the algorithm.

        The inputs and outputs referenced below refer to the parameters of the\
        method or function.

    :param input_definitions:\
        dict of algorithm parameter name to list of types, one for each\
        algorithm parameter
    :type input_definitions: dict of str -> (str or list of str)
    :param outputs:\
        A list of types output from the algorithm that must match the order in\
        which they are returned.
    :type outputs: list of str
    :param algorithm_id:\
        Optional unique id of the algorithm; if not specified, the name of the\
        class or function is used.
    :type algorithm_id: str
    :param required_inputs:\
        Optional list of required algorithm parameter names; if not specified\
        those parameters which have no default values are used.
    :type required_inputs: list of (str or OneOf or AllOf)
    :param optional_inputs:\
        Optional list of optional algorithm parameter names; if not specified\
        those parameters which have default values are used.
    :type optional_inputs: list of (str or OneOf or AllOf)
    :param method:\
        The optional name of the method to call if decorating a class; if not\
        specified, __call__ is used (i.e. it is assumed to be callable).  Must\
        not be used if decorating a function
    :param file_inputs: set of algorithm parameter names that are file names
    """

    def wrap(algorithm):

        # Get the algorithm id
        final_algorithm_id = algorithm_id
        if algorithm_id is None:
            final_algorithm_id = algorithm.__name__

        # Get the details of the method or function
        function = None
        function_name = None
        algorithm_class = None
        is_class_method = False
        module = None
        if inspect.isclass(algorithm):
            function_name = method
            if method is None:
                function_name = "__call__"
            function = getattr(algorithm, function_name)
            is_class_method = True
            algorithm_class = algorithm.__name__
            module = algorithm.__module__
        elif inspect.isfunction(algorithm):
            if method is not None:
                raise exceptions.PacmanConfigurationException(
                    "Cannot specify a method when decorating a function")
            function = algorithm
            function_name = algorithm.__name__
            is_class_method = False
            module = algorithm.__module__
        else:
            raise exceptions.PacmanConfigurationException(
                "Decorating an unknown object type")

        # Get the inputs
        final_required_inputs, final_optional_inputs = \
            _decode_algorithm_details(
                input_definitions, required_inputs, optional_inputs,
                file_inputs, function, has_self=is_class_method)

        # Add the algorithm
        if is_class_method:
            _algorithms.append(PythonClassAlgorithm(
                final_algorithm_id, final_required_inputs,
                final_optional_inputs, outputs, module,
                algorithm_class, function_name))
        else:
            _algorithms.append(PythonFunctionAlgorithm(
                final_algorithm_id, final_required_inputs,
                final_optional_inputs, outputs, module,
                function_name))

        return algorithm
    return wrap


def reset_algorithms():
    """ Reset the list of known algorithms
    """
    global _algorithms
    _algorithms = list()


def get_algorithms():
    """ Get the list of known algorithms
    """
    return _algorithms
