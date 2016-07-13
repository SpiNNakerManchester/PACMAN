from pacman.executor.abstract_input import AbstractInput
from pacman.model.decorators.overrides import overrides
import os


class SingleInput(AbstractInput):
    """ An input that is just one item
    """

    __slots__ = [

        # The name of the input parameter
        "_name",

        # The type of the input parameter
        "_param_types"

        # True if the input is file-based
        "_is_file"
    ]

    def __init__(self, name, param_types, is_file=False):
        """

        :param name: The name of the input parameter
        :type name: str
        :param param_types: The ordered possible types of the input parameter
        :type param_types: list of str
        :param is_file: True if the input is a file
        :type is_file: bool
        """
        self._name = name
        self._param_types = param_types
        self._is_file = is_file

    @property
    @overrides(AbstractInput.name)
    def name(self):
        return self._name

    @property
    @overrides(AbstractInput.param_types)
    def param_types(self):
        return self._param_types

    @property
    def is_file(self):
        return self._is_file

    @overrides(AbstractInput.get_inputs_by_name)
    def get_inputs_by_name(self, inputs):
        for param_type in self._param_types:
            if param_type in inputs:
                param_value = inputs[param_type]

                # If the input is a file, only return true if the file exists
                if (not self._is_file or
                        (self._is_file and
                            os.path.isfile(param_value))):
                    return {self._name: param_value}
        return None

    @overrides(AbstractInput.input_matches)
    def input_matches(self, inputs):
        return any([param_type in inputs for param_type in self._param_types])
