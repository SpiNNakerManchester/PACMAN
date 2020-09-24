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

from pacman.exceptions import PacmanInvalidParameterException


class PartitionTypeAndPreVertices(object):
    """ A Object that holds a traffic type and a set of machine vertexes
    """

    __slots__ = [
        #  The traffic type
        "_traffic_type",
        "_vertices"
    ]

    def __init__(self):
        """
        """
        self._traffic_type = None
        self._vertices = set()

    def add(self, edge):
        """
        Adds the type and data from an edge
        :param MachineEdge edge:
        :raise PacmanInvalidParameterException:
            If the Edge has a traffic type different to ones previously added
        """
        if self._traffic_type is None:
            self._traffic_type = edge.traffic_type
        else:
            if self._traffic_type != edge.traffic_type:
                raise PacmanInvalidParameterException(
                    "edge", edge, "Traffic type is different to previous ones")
        self._vertices.add(edge.pre_vertex)

    @property
    def traffic_type(self):
        return self._traffic_type

    @property
    def vertices(self):
        return self._vertices


