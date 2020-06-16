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
from pacman.model.graphs.graph import Graph
from pacman.model.graphs import OutgoingEdgePartition


class ApplicationGraph(Graph):
    """ An application-level abstraction of a graph.
    """

    __slots__ = [
        # Pointer to the machine_graph created from this graph
        "__machine_graph"]

    def __init__(self, label):
        """
        :param label: The label on the graph, or None
        :type label: str or None
        """
        super(ApplicationGraph, self).__init__(
            ApplicationVertex, ApplicationEdge, OutgoingEdgePartition, label)
        self.__machine_graph = None

    @property
    def machine_graph(self):
        """
        :rtype: MachineGraph
        """
        return self.__machine_graph

    @machine_graph.setter
    def machine_graph(self, machine_graph):
        self.forget_machine_graph()
        self.__machine_graph = machine_graph
        # TRICKY! *Only* place that sets that field to non-None
        machine_graph._app_graph = self

    def forget_machine_graph(self):
        """ Forget the whole mapping from this graph to an application graph.
        """
        for v in self.vertices:
            v.forget_machine_vertices()
        for e in self.edges:
            e.forget_machine_edges()
        self.__machine_graph = None

    def forget_machine_edges(self):
        """ Ensure that all application edges in this graph forget what
            machine edges they map to. The mapping of vertices is unaffected.
        """
        for e in self.edges:
            e.forget_machine_edges()
