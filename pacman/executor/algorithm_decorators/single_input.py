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


class SingleInput(AbstractInput):
    """ An input that is just one item.
    """

    __slots__ = [
        # The name of the input parameter
        "_name",

        # The type of the input parameter
        "_param_types"
    ]

    def __init__(self, name, param_types):
        """
        :param str name: The name of the input parameter
        :param list(str) param_types:
            The ordered possible types of the input parameter
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
