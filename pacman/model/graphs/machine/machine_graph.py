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

from spinn_utilities.default_ordered_dict import DefaultOrderedDict
from spinn_utilities.overrides import overrides
from .machine_vertex import MachineVertex
from .machine_edge import MachineEdge
from pacman.model.graphs.graph import Graph
from pacman.model.graphs import OutgoingEdgePartition
from pacman.model.graphs.common import EdgeTrafficType
from pacman.exceptions import PacmanInvalidParameterException


class MachineGraph(Graph):
    """ A graph whose vertices can fit on the chips of a machine.
    """

    __slots__ = [
        # Flags to say the application level is used so all machine vertices
        # will have an application vertex
        "_application_level_used",
        # A double dictionary of pre machine vertices by their
        # application vertex and then their (partition name)
        "_pre_vertices_by_app_and_partition_name"
    ]

    def __init__(self, label, application_graph=None):
        """
        :param label: The label for the graph.
        :type label: str or None
        :param application_graph:
            The application graph that this machine graph is derived from, if
            it is derived from one at all.
        :type application_graph: ApplicationGraph or None
        """
        super(MachineGraph, self).__init__(
            MachineVertex, MachineEdge, OutgoingEdgePartition, label)
        if application_graph:
            application_graph.forget_machine_graph()
            self._application_level_used = application_graph.n_vertices > 0
        else:
            self._application_level_used = False
        self._pre_vertices_by_app_and_partition_name = DefaultOrderedDict(
            lambda: DefaultOrderedDict(set))

    @overrides(Graph.add_vertex)
    def add_vertex(self, vertex):
        super(MachineGraph, self).add_vertex(vertex)
        if self._application_level_used:
            if vertex.app_vertex is None:
                raise PacmanInvalidParameterException(
                    "vertex", vertex, "The vertex does not have an app_vertex")

    @overrides(Graph.add_edge)
    def add_edge(self, edge, outgoing_edge_partition_name):
        super(MachineGraph, self).add_edge(edge, outgoing_edge_partition_name)
        if self._application_level_used:
            if edge.traffic_type == EdgeTrafficType.MULTICAST:
                by_app = self._pre_vertices_by_app_and_partition_name[
                    edge.pre_vertex.app_vertex]
                by_partition = by_app[outgoing_edge_partition_name]
                by_partition.add(edge.pre_vertex)

    @property
    def multicast_partitions(self):
        """
        Returns a double dictionary of app_vertex then
         outgoing_edge_partition_name to a set of machine_vertex that act as
         pre vertices for these multicast edges
        :rtype dict(ApplicactionVertex, dict(str, set(MachineVertex))
        """
        return self._pre_vertices_by_app_and_partition_name

    @property
    def application_level_used(self):
        """
        Defines if the machine graph as an associated used application graph
        :type bool
        """
        return self._application_level_used
