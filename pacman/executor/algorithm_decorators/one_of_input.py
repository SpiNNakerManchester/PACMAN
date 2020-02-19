# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from spinn_utilities.overrides import overrides
from .abstract_input import AbstractInput


class OneOfInput(AbstractInput):
    """ An input for which one of the input parameters must be matched.
    """

    __slots__ = [
        # The inputs
        "_inputs"
    ]

    def __init__(self, inputs):
        """
        :param list(AbstractInput) inputs:
            The inputs that make up this input
        """
        self._inputs = inputs

    @property
    @overrides(AbstractInput.name)
    def name(self):
        return "One of {}".format(
            [input_type.name for input_type in self._inputs])

    @property
    @overrides(AbstractInput.param_types)
    def param_types(self):
        return "One of {}".format(
            [input_type.param_types for input_type in self._inputs])

    @overrides(AbstractInput.get_inputs_by_name)
    def get_inputs_by_name(self, inputs):
        for input_type in self._inputs:
            match = input_type.get_inputs_by_name(inputs)
            # If the match was found, return it
            if match is not None:
                return match
        return None

    @overrides(AbstractInput.input_matches)
    def input_matches(self, inputs):
        return any(param.input_matches(inputs) for param in self._inputs)

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
        return "OneOfInput(inputs={})".format(self._inputs)
