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


class MachineEdge(AbstractEdge):
    """ A simple implementation of a machine edge.
    """

    __slots__ = [
        # The vertex at the start of the edge
        "_pre_vertex",

        # The vertex at the end of the edge
        "_post_vertex",

        # The label of the edge
        "_label"
    ]

    def __init__(self, pre_vertex, post_vertex, label=None):
        """
        :param MachineVertex pre_vertex: The vertex at the start of the edge.
        :param MachineVertex post_vertex: The vertex at the end of the edge.
        :param label: The name of the edge.
        :type label: str or None
        """
        self._label = label
        self._pre_vertex = pre_vertex
        self._post_vertex = post_vertex

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

    def __repr__(self):
        return (
            "MachineEdge(pre_vertex={}, post_vertex={}, label={})".format(
                self._pre_vertex, self._post_vertex, self.label))
