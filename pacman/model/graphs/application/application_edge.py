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
from spinn_utilities.ordered_set import OrderedSet
from pacman.model.graphs import AbstractEdge
from pacman.model.graphs.common import EdgeTrafficType

_MachineEdge = None


def _machine_edge_class():
    global _MachineEdge  # pylint: disable=global-statement
    if _MachineEdge is None:
        from pacman.model.graphs.machine import MachineEdge
        _MachineEdge = MachineEdge
    return _MachineEdge


class ApplicationEdge(AbstractEdge):
    """ A simple implementation of an application edge.
    """

    __slots__ = [
        # The edge at the start of the vertex
        "_pre_vertex",

        # The edge at the end of the vertex
        "_post_vertex",

        # The type of traffic on the edge
        "_traffic_type",

        # Machine edge type
        "_machine_edge_type",

        # The label
        "_label",

        # Ordered set of associated machine edges
        "__machine_edges"
    ]

    def __init__(
            self, pre_vertex, post_vertex,
            traffic_type=EdgeTrafficType.MULTICAST, label=None,
            machine_edge_type=None):
        """
        :param ApplicationVertex pre_vertex:
            The application vertex at the start of the edge.
        :param ApplicationVertex post_vertex:
            The application vertex at the end of the edge.
        :param EdgeTrafficType traffic_type:
            The type of the traffic on the edge.
        :param str label: The name of the edge.
        :param machine_edge_type:
            The type of machine edges made from this app edge. If `None`,
            standard `MachineEdge`s will be made.
        :type machine_edge_type: type(MachineEdge) or None
        """
        self._label = label
        self._pre_vertex = pre_vertex
        self._post_vertex = post_vertex
        self._traffic_type = traffic_type
        if machine_edge_type is None:
            machine_edge_type = _machine_edge_class()
        # TODO: Enforce the type relationship
        self._machine_edge_type = machine_edge_type
        self.__machine_edges = OrderedSet()

    @property
    @overrides(AbstractEdge.label)
    def label(self):
        return self._label

    # This method gets overridden
    def create_machine_edge(self, pre_vertex, post_vertex, label):
        """ Create a machine edge between two machine vertices that is a
            machine-level embodiment of this application edge.

        :param ~pacman.model.graphs.machine.MachineVertex pre_vertex:
            The machine vertex at the start of the edge.
        :param ~pacman.model.graphs.machine.MachineVertex post_vertex:
            The machine vertex at the end of the edge.
        :param str label: label of the edge
        :return: The created machine edge
        :rtype: ~pacman.model.graphs.machine.MachineEdge
        """
        m_edge = self._machine_edge_type(
            pre_vertex, post_vertex, self._traffic_type, label=label,
            app_edge=self)
        self.remember_associated_machine_edge(m_edge)
        return m_edge

    @property
    @overrides(AbstractEdge.pre_vertex)
    def pre_vertex(self):
        return self._pre_vertex

    @property
    @overrides(AbstractEdge.post_vertex)
    def post_vertex(self):
        return self._post_vertex

    @property
    @overrides(AbstractEdge.traffic_type)
    def traffic_type(self):
        return self._traffic_type

    @property
    def machine_edges(self):
        """ The machine
        :rtype: iterable(MachineEdge)
        """
        return self.__machine_edges

    def remember_associated_machine_edge(self, machine_edge):
        """
        :param MachineEdge machine_edge:
        """
        self.__machine_edges.add(machine_edge)

    def forget_machine_edges(self):
        """ Clear the collection of machine edges created by this application
            edge.
        """
        self.__machine_edges = OrderedSet()
