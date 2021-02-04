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

from collections import OrderedDict
from spinn_utilities.default_ordered_dict import DefaultOrderedDict
from spinn_utilities.ordered_set import OrderedSet
from spinn_utilities.overrides import overrides
from pacman.exceptions import PacmanConfigurationException
from pacman.model.graphs import AbstractEdgePartition


class AbstractMultiplePartition(AbstractEdgePartition):

    __slots__ = [
        # the vertices which send through this partition.
        "_pre_vertices",
        # the destinations of this outgoing partition.
        "_destinations"
    ]

    def __init__(
            self, pre_vertices, identifier, allowed_edge_types, constraints,
            label, traffic_weight, class_name):
        super().__init__(
            identifier=identifier,
            allowed_edge_types=allowed_edge_types, constraints=constraints,
            label=label, traffic_weight=traffic_weight, class_name=class_name)
        self._pre_vertices = OrderedDict()
        self._destinations = DefaultOrderedDict(OrderedSet)

        # hard code dict of lists so that only these are acceptable.
        for pre_vertex in pre_vertices:
            self._pre_vertices[pre_vertex] = OrderedSet()

        # handle clones
        if len(self._pre_vertices.keys()) != len(pre_vertices):
            raise PacmanConfigurationException(
                "There were clones in your list of acceptable pre vertices")

    @overrides(AbstractEdgePartition.add_edge)
    def add_edge(self, edge, graph_code):
        # safety checks
        if edge.pre_vertex not in self._pre_vertices.keys():
            raise Exception(
                "The edge {} is not allowed in this outgoing partition".format(
                    edge))

        # update
        self._pre_vertices[edge.pre_vertex].add(edge)
        self._destinations[edge.post_vertex].add(edge)
        super().add_edge(edge, graph_code)

    @property
    @overrides(AbstractEdgePartition.pre_vertices)
    def pre_vertices(self):
        return self._pre_vertices.keys()
