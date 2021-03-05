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


class SameAtomsAsVertexConstraint(AbstractPartitionerConstraint):
    """ A constraint which indicates that a vertex must be split in the\
        same way as another vertex.
    """

    __slots__ = [
        # The application vertex to which the constraint refers
        "_vertex"
    ]

    def __init__(self, vertex):
        """
        :param ApplicationVertex vertex:
            The vertex to which the constraint refers
        """
        self._vertex = vertex
        raise NotImplementedError(
            "SameAtomsAsVertexConstraint is no longer supported. "
            "Please contact spinnakerusers@googlegroups.com to discuss your "
            "requirements.")

    @property
    def vertex(self):
        """ The vertex to partition with

        :rtype: ApplicationVertex
        """
        return self._vertex

    def __repr__(self):
        return "SameAtomsAsVertexConstraint(vertex={})".format(
            self._vertex)

    def __eq__(self, other):
        if not isinstance(other, SameAtomsAsVertexConstraint):
            return False
        return self._vertex == other.vertex

    def __ne__(self, other):
        if not isinstance(other, SameAtomsAsVertexConstraint):
            return True
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self._vertex,))
