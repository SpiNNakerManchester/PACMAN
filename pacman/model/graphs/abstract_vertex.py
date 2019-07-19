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
class AbstractVertex(object):
    """ A vertex in a graph.
    """

    __slots__ = ()

    @abstractproperty
    def label(self):
        """ The label of the vertex.

        :rtype: str
        """

    @abstractproperty
    def constraints(self):
        """ The constraints of the vertex.

        :rtype: iterable(:py:class:`AbstractConstraint`)
        """

    @abstractmethod
    def add_constraint(self, constraint):
        """ Add a constraint to the vertex.

        :param constraint: The constraint to add
        :type constraint: :py:class:`AbstractConstraint`
        """

    def add_constraints(self, constraints):
        """ Add a list of constraints to the vertex.

        :param constraints: The list of constraints to add
        :type constraints: list(:py:class:`AbstractConstraint`)
        """
        for constraint in constraints:
            self.add_constraint(constraint)
