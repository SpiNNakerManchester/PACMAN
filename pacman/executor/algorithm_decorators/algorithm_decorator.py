# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import inspect
try:
    from inspect import getfullargspec
except ImportError:
    # Python 2.7 hack
    from inspect import getargspec as getfullargspec
import logging
import os
import pkgutil
import sys
from threading import RLock
from six import iteritems
from spinn_utilities.log import FormatAdapter
from spinn_utilities.ordered_set import OrderedSet
from pacman.exceptions import PacmanConfigurationException
from pacman.executor.algorithm_classes import (
    PythonClassAlgorithm, PythonFunctionAlgorithm)
from .one_of_input import OneOfInput
from .output import Output
from .single_input import SingleInput
from .all_of_input import AllOfInput
# pylint: disable=redefined-outer-name, deprecated-method

# The dict of algorithm name to algorithm description
_algorithms = dict()

# A lock of the algorithms
_algorithm_lock = RLock()

logger = FormatAdapter(logging.getLogger(__name__))


class AllOf(object):
    """ Indicates that all of the items specified are required.
    """

    __slots__ = ["_items"]

    def __init__(self, *items):
        """
        :param items: The items required
        :type items: list(str or AllOf or OneOf)
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
    """ Indicates that one of the items specified is required.
    """

    __slots__ = ["_items"]

    def __init__(self, *items):
        """
        :param items: The items required
        :type items: list(str or AllOf or OneOf)
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
    :type input_defs: dict(str, AbstractInput)
    :param inputs: A list of inputs to decode
    :type inputs: list(str or OneOf or AllOf)
    :return: a list of inputs
    :rtype: list(AbstractInput)
    """
    final_inputs = list()
    for inp in inputs:
        if isinstance(inp, str):
            if inp not in input_defs:  # pragma: no cover
                raise PacmanConfigurationException(
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
    :type input_definitions: dict(str, AbstractInput)
    :param required_inputs: List of required algorithm parameter names
    :type required_inputs: list(str or OneOf or AllOf)
    :param optional_inputs: List of optional algorithm parameter names
    :type optional_inputs: list(str or OneOf or AllOf)
    :param callable function: The function to be called by the algorithm
    :param bool has_self: True if the self parameter is expected
    """
    function_args = getfullargspec(function)
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
    for (input_name, input_types) in iteritems(input_definitions):
        if (input_name not in required_args and
                input_name not in optional_args):  # pragma: no cover
            raise PacmanConfigurationException(
                "No parameter named {} but found one"
                " in the input_definitions".format(input_name))
        if not isinstance(input_types, list):
            input_types = [input_types]
        input_defs[input_name] = SingleInput(input_name, input_types)

    # Check that there is a definition for every required argument
    for arg in required_args:
        if arg not in input_defs and (not has_self or arg != "self"):
            raise PacmanConfigurationException(
                "No input_definition for the argument {}".format(arg))

    # Get the required arguments
    final_required_inputs = None
    if required_inputs is None:
        final_required_inputs = [
            input_defs[arg]
            for arg in required_args if not has_self or arg != "self"]
    else:
        final_required_inputs = _decode_inputs(input_defs, required_inputs)

    # Get the optional arguments
    final_optional_inputs = None
    if optional_inputs is None:
        final_optional_inputs = [
            input_defs[arg]
            for arg in optional_args
            if (not has_self or arg != "self") and arg in input_defs]
    else:
        final_optional_inputs = _decode_inputs(input_defs, optional_inputs)

    return final_required_inputs, final_optional_inputs


def algorithm(
        input_definitions, outputs, algorithm_id=None, required_inputs=None,
        optional_inputs=None, method=None, required_input_tokens=None,
        optional_input_tokens=None, generated_output_tokens=None):
    """ A :py:obj:`decorator` that defines an object to be a PACMAN algorithm
        that can be executed by the :py:class:`PACMANAlgorithmExecutor`.

        Can be used to decorate either a class or a function (not a method).\
        If this decorates a class, the class must be callable (i.e., have a\
        ``__call__`` method), or else a method must be specified to call to\
        run the algorithm.

        The inputs and outputs referenced below refer to the parameters of the\
        method or function.

    :param input_definitions:
        dict of algorithm parameter name to list of types, one for each
        required algorithm parameter, and one for each optional parameter
        that is used in this algorithm call
    :type input_definitions: dict(str, str or list(str))
    :param list(str) outputs:
        A list of types output from the algorithm that must match the order in
        which they are returned.
    :param str algorithm_id:
        Optional unique ID of the algorithm; if not specified, the name of the
        class or function is used.
    :param required_inputs:
        Optional list of required algorithm parameter names; if not specified
        those parameters which have no default values are used.
    :type required_inputs: list(str or OneOf or AllOf)
    :param optional_inputs:
        Optional list of optional algorithm parameter names; if not specified\
        those parameters which have default values are used.
    :type optional_inputs: list(str or OneOf or AllOf)
    :param method:
        The optional name of the method to call if decorating a class; if not
        specified, ``__call__`` is used (i.e. it is assumed to be callable).
        Must not be used if decorating a function
    :type method: str or None
    :param list(Token) required_input_tokens:
        A list of tokens required to have been generated before this algorithm
        runs
    :param list(Token) optional_input_tokens:
        A list of tokens that if generated by any algorithm, must have been
        generated before this algorithm runs
    :param list(Token) generated_output_tokens:
        A list of tokens generated by running this algorithm
    """

    def wrap(algorithm):
        # Get the algorithm ID
        algo_id = algorithm_id or algorithm.__name__
        if algo_id in _algorithms:
            raise PacmanConfigurationException(
                "Multiple algorithms with ID {} found: {} and {}".format(
                    algo_id, algorithm, _algorithms[algo_id]))

        # Get the details of the method or function
        if inspect.isclass(algorithm):
            if hasattr(algorithm, "__init__"):
                init = getattr(algorithm, "__init__")
                try:
                    init_args = getfullargspec(init)
                    n_init_defaults = 0
                    if init_args.defaults is not None:
                        n_init_defaults = len(init_args.defaults)
                    if len(init_args.args) - n_init_defaults != 1:
                        raise PacmanConfigurationException(
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
            if method is not None:  # pragma: no cover
                raise PacmanConfigurationException(
                    "Cannot specify a method when decorating a function")
            function = algorithm
            function_name = algorithm.__name__
            algorithm_class = None
            is_class_method = False
            module = algorithm.__module__
        else:  # pragma: no cover
            raise PacmanConfigurationException(
                "Decorating an unknown object type")

        # Get the inputs
        _inputs, _options = _decode_algorithm_details(
            input_definitions, required_inputs, optional_inputs, function,
            has_self=is_class_method)

        # Get the outputs
        # TODO: Support file name type outputs - is there a use case? Note
        # that python algorithms can output the actual file name in the
        # variable
        _outputs = [Output(output_type) for output_type in outputs]

        # https://stackoverflow.com/questions/7338501/python-assign-value-if-none-exists
        _in_toks = required_input_tokens or []
        _opt_toks = optional_input_tokens or []
        _out_toks = generated_output_tokens or []

        # Add the algorithm
        if is_class_method:
            with _algorithm_lock:
                _algorithms[algo_id] = PythonClassAlgorithm(
                    algo_id, _inputs, _options, _outputs, _in_toks, _opt_toks,
                    _out_toks, module, algorithm_class, function_name)
        else:
            with _algorithm_lock:
                _algorithms[algo_id] = PythonFunctionAlgorithm(
                    algo_id, _inputs, _options, _outputs, _in_toks, _opt_toks,
                    _out_toks, module, function_name)

        return algorithm
    return wrap


def algorithms(algorithms):
    """ Specify multiple algorithms for a single class or function

    :param algorithms: A list of algorithm definitions
    :type algorithms: list(algorithm)
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
    """ Get the dict of known algorithm ID -> algorithm data

    :rtype: dict(str, AbstractAlgorithm)
    """
    return _algorithms


def scan_packages(packages, recursive=True):
    """ Scan packages for algorithms

    :param packages:
        The names of the packages to scan (using dotted notation),
        or the actual package modules
    :type packages: list(str or package)
    :param bool recursive: True if sub-packages should be examined
    :return: A dict of algorithm name -> algorithm data
    :rtype: dict(str, AbstractAlgorithm)
    """
    global _algorithms
    # pylint: disable=broad-except

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
                except Exception as ex:  # pragma: no cover
                    logger.warning("Failed to import package {}: {}".format(
                        package_name, str(ex)))
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
                    except Exception as ex:  # pragma: no cover
                        logger.warning("Failed to import module {}: {}".format(
                            module, str(ex)))
                        continue

        new_algorithms = _algorithms
        _algorithms = current_algorithms
        return new_algorithms
