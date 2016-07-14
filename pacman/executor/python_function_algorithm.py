from pacman.executor.abstract_algorithm import AbstractAlgorithm
from pacman.model.decorators.overrides import overrides
from pacman import exceptions

import importlib


class PythonFunctionAlgorithm(AbstractAlgorithm):
    """ An algorithm that is a function
    """

    __slots__ = [

        # Python Module containing the algorithm function
        "_python_module",

        # Python Function to call
        "_python_function"
    ]

    def __init__(
            self, algorithm_id, required_inputs, optional_inputs, outputs,
            python_module, python_function):
        AbstractAlgorithm.__init__(
            self, algorithm_id, required_inputs, optional_inputs, outputs)
        self._python_module = python_module
        self._python_function = python_function

    @overrides(AbstractAlgorithm.call)
    def call(self, inputs):

        # Get the function to call
        function = getattr(
            importlib.import_module(self._python_module),
            self._python_function)

        # Get the inputs to pass to the function
        func_inputs = self._get_inputs(inputs)

        # Run the algorithm and get the results
        results = function(**func_inputs)

        # Return the results processed into a dict
        if len(self._outputs) != len(results):
            raise exceptions.PacmanAlgorithmFailedToGenerateOutputsException(
                "Algorithm {} returned {} items but specified {} output types"
                .format(self._algorithm_id, len(results), len(self._outputs)))
        return {
            output_type: result
            for (output_type, result) in zip(self._outputs, results)
        }
