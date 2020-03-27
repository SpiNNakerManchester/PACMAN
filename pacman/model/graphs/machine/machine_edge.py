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
from pacman.model.graphs.common import EdgeTrafficType
from pacman.model.graphs import AbstractEdge


class MachineEdge(AbstractEdge):
    """ A simple implementation of a machine edge.
    """

    __slots__ = [
        # The vertex at the start of the edge
        "_pre_vertex",

        # The vertex at the end of the edge
        "_post_vertex",

        # The type of traffic for this edge
        "_traffic_type",

        # The traffic weight of the edge
        "_traffic_weight",

        # The label of the edge
        "_label"
    ]

    def __init__(
            self, pre_vertex, post_vertex,
            traffic_type=EdgeTrafficType.MULTICAST, label=None,
            traffic_weight=1):
        """
        :param MachineVertex pre_vertex: The vertex at the start of the edge.
        :param MachineVertex post_vertex: The vertex at the end of the edge.
        :param EdgeTrafficType traffic_type:
            The type of traffic that this edge will carry.
        :param str label: The name of the edge.
        :param int traffic_weight:
            The optional weight of traffic expected to travel down this edge
            relative to other edges. (default is 1)
        """
        self._label = label
        self._pre_vertex = pre_vertex
        self._post_vertex = post_vertex
        self._traffic_type = traffic_type
        self._traffic_weight = traffic_weight

    @property
    @overrides(AbstractEdge.label)
    def label(self):
        return self._label

    @property
    @overrides(AbstractEdge.pre_vertex, extend_doc=False)
    def pre_vertex(self):
        """ The vertex at the start of the edge.

        :rtype: ~pacman.model.graphs.machine.MachineVertex
        """
        return self._pre_vertex

    @property
    @overrides(AbstractEdge.post_vertex, extend_doc=False)
    def post_vertex(self):
        """ The vertex at the end of the edge.

        :rtype: ~pacman.model.graphs.machine.MachineVertex
        """
        return self._post_vertex

    @property
    @overrides(AbstractEdge.traffic_type)
    def traffic_type(self):
        return self._traffic_type

    @property
    def traffic_weight(self):
        """ The amount of traffic expected to go down this edge relative to
            other edges.

        :rtype: int
        """
        return self._traffic_weight

    def __repr__(self):
        return (
            "MachineEdge(pre_vertex={}, post_vertex={}, "
            "traffic_type={}, label={}, traffic_weight={})".format(
                self._pre_vertex, self._post_vertex, self._traffic_type,
                self.label, self._traffic_weight))
