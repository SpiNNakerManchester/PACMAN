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

from .abstract_placer_constraint import AbstractPlacerConstraint


class SameChipAsConstraint(AbstractPlacerConstraint):
    """ Indicates that a vertex should be placed on the same chip as another\
        vertex.
    """

    __slots__ = [
        #  The vertex to place on the same chip
        "_vertex"
    ]

    def __init__(self, vertex):
        """
        :param AbstractVertex vertex: The vertex to place on the same chip
        """
        self._vertex = vertex

    @property
    def vertex(self):
        """ The other vertex that we are constraining to cohabit a chip with.

        :rtype: AbstractVertex
        """
        return self._vertex

    def __repr__(self):
        return "SameChipAsConstraint(vertex={})".format(self._vertex)

    def __eq__(self, other):
        if not isinstance(other, SameChipAsConstraint):
            return False
        return self._vertex == other.vertex

    def __ne__(self, other):
        if not isinstance(other, SameChipAsConstraint):
            return True
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self._vertex, ))
