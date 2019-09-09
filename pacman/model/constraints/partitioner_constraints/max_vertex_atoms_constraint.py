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

from .abstract_partitioner_constraint import AbstractPartitionerConstraint


class MaxVertexAtomsConstraint(AbstractPartitionerConstraint):
    """ A constraint which limits the number of atoms on each division of a\
        vertex.
    """

    __slots__ = [
        # The maximum number of atoms to split the application vertex into
        "_size"
    ]

    def __init__(self, size):
        """
        :param size: The maximum number of atoms to split the vertex into
        :type size: int
        """
        self._size = size

    @property
    def size(self):
        """ The maximum number of atoms to split the vertex into

        :rtype: int
        """
        return self._size

    def __repr__(self):
        return "MaxVertexAtomsConstraint(size={})".format(self._size)

    def __eq__(self, other):
        if not isinstance(other, MaxVertexAtomsConstraint):
            return False
        return self._size == other.size

    def __ne__(self, other):
        if not isinstance(other, MaxVertexAtomsConstraint):
            return True
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self._size,))
