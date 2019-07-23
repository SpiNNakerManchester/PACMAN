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

from six import add_metaclass
from spinn_utilities.abstract_base import (
    AbstractBase, abstractmethod, abstractproperty)


@add_metaclass(AbstractBase)
class AbstractInput(object):
    """ An abstract input to an algorithm
    """

    __slots__ = []

    @abstractproperty
    def name(self):
        """ The name of the input
        """

    @abstractproperty
    def param_types(self):
        """ The types of the input
        """

    @abstractmethod
    def get_inputs_by_name(self, inputs):
        """ Get the inputs that match this input by parameter name

        :param inputs: A dict of type to value
        :return: A dict of parameter name to value
        :rtype: dict
        """

    @abstractmethod
    def input_matches(self, inputs):
        """ Determine if this input is in the set of inputs

        :param inputs: A set of input types
        :return: True if this input type is in the list
        """

    @abstractmethod
    def get_fake_inputs(self, inputs):
        """ Get input types that are not in inputs but which satisfy this input

        :param inputs: A set of input types
        :return:\
            A set of input parameter names that are not available in inputs
        """

    @abstractmethod
    def get_matching_inputs(self, inputs):
        """ Get input types that are in inputs and satisfy this input

        :param inputs: A set of input types
        :return:\
            A set of input parameter names that are available in inputs
        """
