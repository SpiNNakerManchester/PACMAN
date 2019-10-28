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

from pacman.exceptions import PacmanConfigurationException
from pacman.model.graphs import AbstractEdgePartition


class AbstractSingleSourcePartition(AbstractEdgePartition):

    __slots__ = [
        "_pre_vertex"
    ]

    def __init__(
            self, pre_vertex, identifier, allowed_edge_types, constraints,
            label, traffic_weight, class_name):
        AbstractEdgePartition.__init__(
            self, identifier=identifier,
            allowed_edge_types=allowed_edge_types, constraints=constraints,
            label=label, traffic_weight=traffic_weight,
            class_name=class_name)
        self._pre_vertex = pre_vertex

    def add_edge(self, edge):
        if edge.pre_vertex != self._pre_vertex:
            raise PacmanConfigurationException(
                "A partition can only contain edges with the same pre_vertex")
        AbstractEdgePartition.add_edge(self, edge)

    @property
    def pre_vertex(self):
        return self._pre_vertex
