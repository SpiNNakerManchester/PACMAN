from abc import abstractmethod
from spinn_utilities.overrides import overrides
from pacman.exceptions import PacmanAlgorithmFailedToGenerateOutputsException
from .abstract_algorithm import AbstractAlgorithm


class AbstractPythonAlgorithm(AbstractAlgorithm):
    """ An algorithm written in Python
    """

    __slots__ = [
        # The module containing the python code to execute
        "_python_module"
    ]

    def __init__(
            self, algorithm_id, required_inputs, optional_inputs, outputs,
            required_input_tokens, optional_input_tokens,
            generated_output_tokens, python_module):
        """

        :param python_module: The module containing the python code to execute
        """
        # pylint: disable=too-many-arguments
        super(AbstractPythonAlgorithm, self).__init__(
            algorithm_id, required_inputs, optional_inputs, outputs,
            required_input_tokens, optional_input_tokens,
            generated_output_tokens)
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
        if results is None and not self._outputs:
            return None

        # Check the results are valid
        if ((results is None and self._outputs) or
                len(self._outputs) != len(results)):
            raise PacmanAlgorithmFailedToGenerateOutputsException(
                "Algorithm {} returned {} but specified {} output types"
                .format(self._algorithm_id, results, len(self._outputs)))

        # Return the results processed into a dict
        return self._get_outputs(inputs, results)
