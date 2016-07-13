from pacman.executor.abstract_algorithm import AbstractAlgorithm
from pacman.model.decorators.overrides import overrides
import importlib


class PythonClassAlgorithm(AbstractAlgorithm):
    """ An algorithm that is a class
    """

    __slots__ = [

        # Python Module containing the algorithm function
        "_python_module",

        # Python Class to create
        "_python_class",

        # Python Method to call on the class (optional if class is callable)
        "_python_method"
    ]

    def __init__(
            self, algorithm_id, required_inputs, optional_inputs, outputs,
            python_module, python_class, python_method=None):
        AbstractAlgorithm.__init__(
            self, algorithm_id, required_inputs, optional_inputs, outputs)
        self._python_module = python_module
        self._python_class = python_class
        self._python_method = python_method

    @overrides(AbstractAlgorithm.call)
    def call(self, inputs):

        # Get the class to use
        cls = getattr(
            importlib.import_module(self._python_module),
            self._python_class)

        # Create an instance
        instance = cls()

        # Get the method to call (or use the class as a callable if None)
        method = instance
        if self._python_method is not None:
            method = getattr(instance, method)

        # Get the inputs to pass to the function
        method_inputs = self._get_inputs(inputs)

        # Run the algorithm and get the results
        results = method(**method_inputs)

        # Return the results processed into a dict
        return {
            output_type: result
            for (output_type, result) in zip(self._outputs, results)
        }
