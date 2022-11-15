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
from pacman.model.graphs import AbstractSingleSourcePartition
from .application_edge import ApplicationEdge


class ApplicationEdgePartition(AbstractSingleSourcePartition):
    """ A simple implementation of an application edge partition that will\
        communicate using SpiNNaker multicast packets. They have the same \
        source(s) and semantics and so can share a single key.
    """

    __slots__ = ()

    def __init__(self, identifier, pre_vertex):
        """
        :param str identifier: The identifier of the partition
        :param ApplicationVertex pre_vertex: The source of this partition
        """
        super().__init__(
            pre_vertex=pre_vertex, identifier=identifier,
            allowed_edge_types=ApplicationEdge)

    @overrides(AbstractSingleSourcePartition.add_edge)
    def add_edge(self, edge):
        super().add_edge(edge)
        edge.post_vertex.add_incoming_edge(edge, self)
