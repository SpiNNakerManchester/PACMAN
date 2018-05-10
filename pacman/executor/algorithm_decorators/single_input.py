from spinn_utilities.overrides import overrides
from .abstract_input import AbstractInput


class SingleInput(AbstractInput):
    """ An input that is just one item
    """

    __slots__ = [
        # The name of the input parameter
        "_name",

        # The type of the input parameter
        "_param_types"
    ]

    def __init__(self, name, param_types):
        """

        :param name: The name of the input parameter
        :type name: str
        :param param_types: The ordered possible types of the input parameter
        :type param_types: list of str
        """
        self._name = name
        self._param_types = param_types

    @property
    @overrides(AbstractInput.name)
    def name(self):
        return self._name

    @property
    @overrides(AbstractInput.param_types)
    def param_types(self):
        return self._param_types

    @overrides(AbstractInput.get_inputs_by_name)
    def get_inputs_by_name(self, inputs):
        for param_type in self._param_types:
            if param_type in inputs:
                return {self._name: inputs[param_type]}
        return None

    @overrides(AbstractInput.input_matches)
    def input_matches(self, inputs):
        return any(param_type in inputs for param_type in self._param_types)

    @overrides(AbstractInput.get_fake_inputs)
    def get_fake_inputs(self, inputs):
        return {
            param_type for param_type in self._param_types
            if param_type not in inputs
        }

    @overrides(AbstractInput.get_matching_inputs)
    def get_matching_inputs(self, inputs):
        return {
            param_type for param_type in self._param_types
            if param_type in inputs
        }

    def __repr__(self):
        return "SingleInput(name={}, param_types={})".format(
            self._name, self._param_types)
