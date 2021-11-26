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
from pacman.model.graphs import AbstractEdge


class ApplicationEdge(AbstractEdge):
    """ A simple implementation of an application edge.
    """

    __slots__ = [
        # The edge at the start of the vertex
        "_pre_vertex",

        # The edge at the end of the vertex
        "_post_vertex",

        # The label
        "_label"
    ]

    def __init__(
            self, pre_vertex, post_vertex, label=None):
        """
        :param ApplicationVertex pre_vertex:
            The application vertex at the start of the edge.
        :param ApplicationVertex post_vertex:
            The application vertex at the end of the edge.
        :param label: The name of the edge.
        :type label: str or None
        :param machine_edge_type:
            The type of machine edges made from this app edge. If ``None``,
            standard machine edges will be made.
        :type machine_edge_type: type(MachineEdge)
        """
        self._label = label
        self._pre_vertex = pre_vertex
        self._post_vertex = post_vertex

    @property
    @overrides(AbstractEdge.label)
    def label(self):
        return self._label

    @property
    @overrides(AbstractEdge.pre_vertex)
    def pre_vertex(self):
        return self._pre_vertex

    @property
    @overrides(AbstractEdge.post_vertex)
    def post_vertex(self):
        return self._post_vertex
