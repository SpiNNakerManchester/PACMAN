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
from pacman.exceptions import PacmanConfigurationException
from .machine_graph import MachineGraph


class MachineGraphView(MachineGraph):
    """ A frozen view of a Machine Graph

    As this shares all the same objects as the graph it is a view over except
    for the class and id. So any changes to the other are reflected.

    All methods that allow changes to the graph should be disabled.
    """

    __slots__ = []

    def __init__(self, other):
        super().__init__(other.label)
        # Reused the objects as they are unmutable and may be keys
        self._vertices = other._vertices
        self._vertex_by_label = other._vertex_by_label
        # should never be needed
        self._unlabelled_vertex_count = None
        self._incoming_edges = other._incoming_edges
        self._application_level_used = other._application_level_used
        self._fixed_route_edge_partitions_by_pre_vertex = \
            other._fixed_route_edge_partitions_by_pre_vertex
        self._multicast_edge_partitions_by_pre_vertex = \
            other._multicast_edge_partitions_by_pre_vertex
        self._sdram_edge_partitions_by_post_vertex = \
            other._sdram_edge_partitions_by_post_vertex
        self._n_outgoing_edge_partitions = other._n_outgoing_edge_partitions

    @overrides(MachineGraph.add_edge)
    def add_edge(self, edge, outgoing_edge_partition_name):
        raise PacmanConfigurationException(
            "Please add edges via simulator not directly to this graph")

    @overrides(MachineGraph.add_vertex)
    def add_vertex(self, vertex):
        raise PacmanConfigurationException(
            "Please add vertices via simulator not directly to this graph")

    @overrides(MachineGraph.add_outgoing_edge_partition)
    def add_outgoing_edge_partition(self, edge_partition):
        raise PacmanConfigurationException(
            "Please add partitions via simulator not directly to this graph")
