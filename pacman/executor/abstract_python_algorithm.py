from pacman.executor.abstract_algorithm import AbstractAlgorithm
from pacman.model.decorators.overrides import overrides
from pacman import exceptions

from abc import abstractmethod


class AbstractPythonAlgorithm(AbstractAlgorithm):
    """ An algorithm written in Python
    """

    @overrides(AbstractAlgorithm.__init__)
    def __init__(
            self, algorithm_id, required_inputs, optional_inputs, outputs,
            python_module):
        """
        :param python_module: The module containing the python code to execute
        """
        AbstractAlgorithm.__init__(
            self, algorithm_id, required_inputs, optional_inputs, outputs)
        self._python_module = python_module

    @abstractmethod
    def call_python(self, inputs):
        """ Call the algorithm

        :param inputs: A dict of parameter name -> value
        :return: The result of calling the python algorithm
        """

    @overrides(AbstractAlgorithm.call)
    def call(self, inputs):

        # Get the inputs to pass to the function
        method_inputs = self._get_inputs(inputs)

        # Run the algorithm and get the results
        results = self.call_python(method_inputs)

        if results is not None and not isinstance(results, tuple):
            results = (results,)

        # If there are no results and there are not meant to be, return
        if results is None and len(self._outputs) == 0:
            return None

        # Check the results are valid
        if ((results is None and len(self._outputs) > 0) or
                len(self._outputs) != len(results)):
            raise exceptions.PacmanAlgorithmFailedToGenerateOutputsException(
                "Algorithm {} returned {} but specified {} output types"
                .format(self._algorithm_id, results, len(self._outputs)))

        # Return the results processed into a dict
        return self._get_outputs(inputs, results)
