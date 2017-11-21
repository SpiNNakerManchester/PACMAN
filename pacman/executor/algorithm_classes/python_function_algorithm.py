import importlib
import sys
import logging

from .abstract_python_algorithm import AbstractPythonAlgorithm
from pacman.model.decorators import overrides

logger = logging.getLogger(__name__)


class PythonFunctionAlgorithm(AbstractPythonAlgorithm):
    """ An algorithm that is a function
    """

    __slots__ = [

        # Python Function to call
        "_python_function"
    ]

    @overrides(AbstractPythonAlgorithm.__init__)
    def __init__(
            self, algorithm_id, required_inputs, optional_inputs, outputs,
            required_input_tokens, generated_output_tokens,
            python_module, python_function):
        """
        :python_function: The name of the function to call
        """
        AbstractPythonAlgorithm.__init__(
            self, algorithm_id, required_inputs, optional_inputs, outputs,
            required_input_tokens, generated_output_tokens, python_module)
        self._python_function = python_function

    @overrides(AbstractPythonAlgorithm.call_python)
    def call_python(self, inputs):

        # Get the function to call
        function = getattr(
            importlib.import_module(self._python_module),
            self._python_function)

        # Run the algorithm and get the results
        try:
            return function(**inputs)
        except Exception:
            exc_type, exc_value, exc_trace = sys.exc_info()
            logger.error("Error when calling {}.{} with inputs {}".format(
                self._python_module, self._python_function, inputs))
            raise exc_type, exc_value, exc_trace

    def __repr__(self):
        return (
            "PythonFunctionAlgorithm(algorithm_id={},"
            " required_inputs={}, optional_inputs={}, outputs={}"
            " python_module={},  python_function={})".format(
                self._algorithm_id, self._required_inputs,
                self._optional_inputs, self._outputs, self._python_module,
                self._python_function))

    @overrides(AbstractPythonAlgorithm.write_provenance_header)
    def write_provenance_header(self, provenance_file):
        provenance_file.write("{}\n".format(self._algorithm_id))
        provenance_file.write("\t{}.{}\n".format(self._python_module,
                                                 self._python_function))
