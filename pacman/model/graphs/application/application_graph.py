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
from .application_edge import ApplicationEdge
from .application_vertex import ApplicationVertex
from .application_edge_partition import ApplicationEdgePartition
from pacman.model.graphs.graph import Graph
from pacman.model.graphs import AbstractEdgePartition


class ApplicationGraph(Graph):
    """ An application-level abstraction of a graph.
    """

    __slots__ = []

    def __init__(self, label):
        """
        :param label: The label on the graph, or None
        :type label: str or None
        """
        super(ApplicationGraph, self).__init__(
            ApplicationVertex, ApplicationEdge, AbstractEdgePartition, label,
            ApplicationEdgePartition)

    def forget_machine_graph(self):
        """ Forget the whole mapping from this graph to an application graph.
        """
        for v in self.vertices:
            v.forget_machine_vertices()
        for e in self.edges:
            e.forget_machine_edges()

    def forget_machine_edges(self):
        """ Ensure that all application edges in this graph forget what
            machine edges they map to. The mapping of vertices is unaffected.
        """
        for e in self.edges:
            e.forget_machine_edges()
