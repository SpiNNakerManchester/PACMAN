# Copyright (c) 2019-2020 The University of Manchester
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
from spinn_utilities.abstract_base import AbstractBase
from spinn_utilities.overrides import overrides
from pacman.exceptions import PacmanConfigurationException
from pacman.model.graphs import AbstractEdgePartition


@add_metaclass(AbstractBase)
class AbstractSingleSourcePartition(AbstractEdgePartition):
    __slots__ = [
        # The vertex at the start of all the edges
        "_pre_vertex"
    ]

    def __init__(
            self, pre_vertex, identifier, allowed_edge_types, constraints,
            label, traffic_weight, class_name):
        super(AbstractSingleSourcePartition, self).__init__(
            identifier=identifier, allowed_edge_types=allowed_edge_types,
            constraints=constraints, label=label,
            traffic_weight=traffic_weight, class_name=class_name)
        self._pre_vertex = pre_vertex

    @overrides(AbstractEdgePartition.add_edge)
    def add_edge(self, edge, graph_code):
        """ Add an edge to the edge partition.

        :param AbstractEdge edge: the edge to add
        :raises PacmanInvalidParameterException:
            If the starting vertex of the edge does not match that of the
            edges already in the partition
        """
        if edge.pre_vertex != self._pre_vertex:
            raise PacmanConfigurationException(
                "A partition can only contain edges with the same pre_vertex")
        super(AbstractSingleSourcePartition, self).add_edge(edge, graph_code)

    @property
    def pre_vertex(self):
        """ The vertex at which all edges in this outgoing edge partition\
            start.

        :rtype: AbstractVertex
        """
        return self._pre_vertex

    @property
    @overrides(AbstractEdgePartition.pre_vertices)
    def pre_vertices(self):
        yield self.pre_vertex
