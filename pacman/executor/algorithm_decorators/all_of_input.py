from .abstract_input import AbstractInput
from spinn_utilities.overrides import overrides


class AllOfInput(AbstractInput):
    """ A composite input for which all input parameters must be matched.
    """

    __slots__ = [
        # The inputs
        "_inputs"
    ]

    def __init__(self, inputs):
        """
        :param inputs: The inputs that make up this input
        """
        self._inputs = inputs

    @property
    @overrides(AbstractInput.name)
    def name(self):
        return "All of {}".format(
            [input_type.name for input_type in self._inputs])

    @property
    @overrides(AbstractInput.param_types)
    def param_types(self):
        return "All of {}".format(
            [input_type.param_types for input_type in self._inputs])

    @overrides(AbstractInput.get_inputs_by_name)
    def get_inputs_by_name(self, inputs):
        matches = dict()
        for input_type in self._inputs:
            match = input_type.get_inputs_by_name(inputs)

            # If the match cannot be found, the whole input is compromised
            if match is None:
                return None
            matches.update(match)
        return matches

    @overrides(AbstractInput.input_matches)
    def input_matches(self, inputs):
        return all(param.input_matches(inputs) for param in self._inputs)

    @overrides(AbstractInput.get_fake_inputs)
    def get_fake_inputs(self, inputs):
        fake_inputs = set()
        for param in self._inputs:
            fake_inputs.update(param.get_fake_inputs(inputs))
        return fake_inputs

    @overrides(AbstractInput.get_matching_inputs)
    def get_matching_inputs(self, inputs):
        matching_inputs = set()
        for param in self._inputs:
            matching_inputs.update(param.get_matching_inputs(inputs))
        return matching_inputs

    def __repr__(self):
        return "AllOfInput(inputs={})".format(self._inputs)
