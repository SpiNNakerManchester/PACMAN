import importlib

from pacman.executor.algorithm_classes.abstract_python_algorithm \
    import AbstractPythonAlgorithm
from pacman.model.decorators.overrides import overrides


class PythonFunctionAlgorithm(AbstractPythonAlgorithm):
    """ An algorithm that is a function
    """

    __slots__ = [

        # Python Module containing the algorithm function
        "_python_module",

        # Python Function to call
        "_python_function"
    ]

    @overrides(AbstractPythonAlgorithm.__init__)
    def __init__(
            self, algorithm_id, required_inputs, optional_inputs, outputs,
            python_module, python_function):
        """
        :python_function: The name of the function to call
        """
        AbstractPythonAlgorithm.__init__(
            self, algorithm_id, required_inputs, optional_inputs, outputs,
            python_module)
        self._python_function = python_function

    @overrides(AbstractPythonAlgorithm.call_python)
    def call_python(self, inputs):

        # Get the function to call
        function = getattr(
            importlib.import_module(self._python_module),
            self._python_function)

        # Run the algorithm and get the results
        return function(**inputs)

    def __repr__(self):
        return (
            "PythonFunctionAlgorithm(algorithm_id={},"
            " required_inputs={}, optional_inputs={}, outputs={}"
            " python_module={},  python_function={})".format(
                self._algorithm_id, self._required_inputs,
                self._optional_inputs, self._outputs, self._python_module,
                self._python_function))
