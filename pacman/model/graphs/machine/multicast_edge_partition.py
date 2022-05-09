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
from pacman.model.graphs import AbstractSingleSourcePartition
from pacman.model.graphs.machine.machine_edge import MachineEdge


class MulticastEdgePartition(AbstractSingleSourcePartition):
    """ A simple implementation of a machine edge partition that will \
        communicate with SpiNNaker multicast packets. They have a common set \
        of sources with the same semantics and so can share a single key.
    """

    __slots__ = ()

    def __init__(self, pre_vertex, identifier):
        """
        :param pre_vertex: the pre vertex of this partition.
        :param str identifier: The identifier of the partition
        """
        super().__init__(
            pre_vertex=pre_vertex, identifier=identifier,
            allowed_edge_types=MachineEdge)

    def __repr__(self):
        return (f"MulticastEdgePartition(pre_vertex={self.pre_vertex},"
                f" identifier={self.identifier})")
