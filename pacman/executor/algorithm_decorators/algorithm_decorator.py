import inspect
import logging
import os
import pkgutil
import sys
from threading import RLock

from pacman.executor.algorithm_decorators.one_of_input import OneOfInput
from pacman.executor.algorithm_decorators.output import Output
from pacman.executor.algorithm_classes.python_function_algorithm \
    import PythonFunctionAlgorithm
from pacman.executor.algorithm_decorators.single_input import SingleInput

from pacman import exceptions
from pacman.executor.algorithm_classes.python_class_algorithm \
    import PythonClassAlgorithm
from pacman.executor.algorithm_decorators.all_of_input import AllOfInput
from spinn_machine.utilities.ordered_set import OrderedSet

# The dict of algorithm name to algorithm description
_algorithms = dict()

# A lock of the algorithms
_algorithm_lock = RLock()

logger = logging.getLogger(__name__)

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
        function, has_self=False):
    """ Convert the algorithm annotation inputs to input classes

    :param input_definitions: dict of algorithm parameter name to list of types
    :param required_inputs: List of required algorithm parameter names
    :type required_inputs: list of str, OneOf, AllOf
    :param optional_inputs: List of optional algorithm parameter names
    :type optional_inputs: list of str, OneOf, AllOf
    :param function: The function to be called by the algorithm
    :param has_self: True if the self parameter is expected
    """
    function_args = inspect.getargspec(function)
    required_args = None
    optional_args = None
    if function_args.defaults is not None:
        n_defaults = len(function_args.defaults)
        required_args = OrderedSet(
            function_args.args[:-n_defaults])
        optional_args = OrderedSet(
            function_args.args[-n_defaults:])
    else:
        required_args = OrderedSet(function_args.args)
        optional_args = OrderedSet()

    # Parse the input definitions
    input_defs = dict()
    for (input_name, input_types) in input_definitions.iteritems():
        if (input_name not in required_args and
                input_name not in optional_args):
            raise exceptions.PacmanConfigurationException(
                "No parameter named {} but found one"
                " in the input_definitions".format(input_name))
        if not isinstance(input_types, list):
            input_types = [input_types]
        input_defs[input_name] = SingleInput(input_name, input_types)

    # Check that there is a definition for every required argument
    for arg in required_args:
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
            if (not has_self or arg != "self") and arg in input_defs
        ]
    else:
        final_optional_inputs = _decode_inputs(input_defs, optional_inputs)

    return final_required_inputs, final_optional_inputs


def algorithm(
        input_definitions, outputs, algorithm_id=None, required_inputs=None,
        optional_inputs=None, method=None):
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
        required algorithm parameter, and one for each optional parameter\
        that is used in this algorithm call
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
    """

    def wrap(algorithm):

        # Get the algorithm id
        final_algorithm_id = algorithm_id
        if algorithm_id is None:
            final_algorithm_id = algorithm.__name__

        if algorithm_id in _algorithms:
            raise exceptions.PacmanConfigurationException(
                "Multiple algorithms with id {} found: {} and {}".format(
                    algorithm_id, algorithm, _algorithms[algorithm_id]))

        # Get the details of the method or function
        function = None
        function_name = None
        algorithm_class = None
        is_class_method = False
        module = None
        if inspect.isclass(algorithm):
            if hasattr(algorithm, "__init__"):
                init = getattr(algorithm, "__init__")
                try:
                    init_args = inspect.getargspec(init)
                    n_init_defaults = 0
                    if init_args.defaults is not None:
                        n_init_defaults = len(init_args.defaults)
                    if (len(init_args.args) - n_init_defaults) != 1:
                        raise exceptions.PacmanConfigurationException(
                            "Algorithm class initialiser cannot take"
                            " arguments")
                except TypeError:
                    # Occurs if no __init__ is defined in class
                    pass
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
                function, has_self=is_class_method)

        # Get the outputs
        # TODO: Support file name type outputs - is there a use case? Note
        # that python algorithms can output the actual file name in the
        # variable
        final_outputs = [Output(output_type) for output_type in outputs]

        # Add the algorithm
        if is_class_method:
            with _algorithm_lock:
                _algorithms[final_algorithm_id] = PythonClassAlgorithm(
                    final_algorithm_id, final_required_inputs,
                    final_optional_inputs, final_outputs, module,
                    algorithm_class, function_name)
        else:
            with _algorithm_lock:
                _algorithms[final_algorithm_id] = PythonFunctionAlgorithm(
                    final_algorithm_id, final_required_inputs,
                    final_optional_inputs, final_outputs, module,
                    function_name)

        return algorithm
    return wrap


def algorithms(algorithms):
    """ Specify multiple algorithms for a single class or function

    :param algorithms: A list of algorithm definitions
    """

    def wrap(alg):
        for alg_def in algorithms:
            alg_def(alg)
        return alg

    return wrap


def reset_algorithms():
    """ Reset the known algorithms
    """
    global _algorithms
    with _algorithm_lock:
        _algorithms = dict()


def get_algorithms():
    """ Get the dict of known algorithm id -> algorithm data
    """
    return _algorithms


def scan_packages(packages, recursive=True):
    """ Scan packages for algorithms

    :param packages:\
        The names of the packages to scan (using dotted notation),
        or the actual package modules
    :param recursive: True if sub-packages should be examined
    :return: A dict of algorithm name -> algorithm data
    """
    global _algorithms

    with _algorithm_lock:
        current_algorithms = _algorithms
        _algorithms = dict()

        # Go through the packages
        for package_name in packages:

            # Import the package
            package = package_name
            if isinstance(package_name, str):
                try:
                    __import__(package_name)
                    package = sys.modules[package_name]
                except Exception as ex:
                    msg = "Failed to import " + package_name + " : " + str(ex)
                    logger.warning(msg)
                    continue
            pkg_path = os.path.dirname(package.__file__)

            # Go through the modules and import them
            for _, name, is_pkg in pkgutil.iter_modules([pkg_path]):

                # If recursive and this is a package, recurse
                module = package.__name__ + "." + name
                if is_pkg and recursive:
                    scan_packages([module], recursive)
                else:
                    try:
                        __import__(module)
                    except Exception as ex:
                        msg = "Failed to import " + module + " : " + str(ex)
                        logger.warning(msg)
                        continue

        new_algorithms = _algorithms
        _algorithms = current_algorithms
        return new_algorithms
