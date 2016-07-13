from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod
from pacman.exceptions import PacmanConfigurationException


@add_metaclass(ABCMeta)
class AbstractAlgorithm(object):
    """ Represents the metadata for an algorithm
    """

    __slots__ = [

        # The id of the algorithm; must be unique over all algorithms
        "_algorithm_id",

        # A list of inputs that must be provided
        "_required_inputs",

        # A list of inputs that can optionally be provided
        "_optional_inputs",

        # A list of output types
        "_outputs"
    ]

    def __init__(
            self, algorithm_id, required_inputs, optional_inputs, outputs):
        """

        :param algorithm_id: The unique id of the algorithm
        :type algorithm_id: str
        :param required_inputs: The inputs required by the algorithm
        :type required_inputs: list of AbstractInput
        :param optional_inputs:\
            The optional inputs for the algorithm, which will be provided\
            when available
        :type optional_inputs: list of AbstractInput
        :param outputs: The output types of the algorithm
        :type outputs: list of str
        """
        self._algorithm_id = algorithm_id
        self._required_inputs = required_inputs
        self._optional_inputs = optional_inputs
        self._outputs = outputs

    @property
    def algorithm_id(self):
        """ The id for this algorithm
        """
        return self._algorithm_id

    @property
    def required_inputs(self):
        """ The required inputs of the algorithm
        """
        return self._required_inputs

    @property
    def optional_inputs(self):
        """ The optional inputs of the algorithm
        """
        return self._optional_inputs

    @property
    def outputs(self):
        """ The output types of the algorithm
        """
        return self._outputs

    def _get_inputs(self, inputs):
        """ Get the required and optional inputs out of the inputs

        :param inputs: A dict of type to value
        :return: A dict of parameter name to value
        """
        matches = dict()

        # Add required inputs, failing if they don't exist
        for required_input in self._required_inputs:
            match = required_input.get_inputs_by_name(inputs)
            if match is None:
                raise PacmanConfigurationException(
                    "Missing required input {} of type {} for algorithm {}"
                    .format(
                        required_input.name, required_input.param_types,
                        self._algorithm_id))
            matches.update(match)

        # Add optional inputs if they exist
        for optional_input in self._optional_inputs:
            match = optional_input.get_inputs_by_name(inputs)
            if match is not None:
                matches.update(match)
        return matches

    @abstractmethod
    def call(self, inputs):
        """ Call the algorithm with the given inputs and return the outputs
        """
