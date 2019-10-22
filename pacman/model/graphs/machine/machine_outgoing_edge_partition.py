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

from pacman.model.graphs.impl import OutgoingEdgePartition
from spinn_utilities.overrides import overrides
from .machine_edge import MachineEdge


class MachineOutgoingEdgePartition(OutgoingEdgePartition):
    """ An outgoing edge partition for a Machine Graph.
    """

    __slots__ = []

    def __init__(self, identifier, pre_vertex, constraints=None, label=None,
                 traffic_weight=1):
        """
        :param identifier: The identifier of the partition
        :param constraints: Any initial constraints
        :param pre_vertex: the pre vertex for this partition
        :param label: An optional label of the partition
        :param traffic_weight: the weight of this partition in relation\
            to other partitions
        """
        super(MachineOutgoingEdgePartition, self).__init__(
            identifier, MachineEdge, pre_vertex, constraints, label,
            traffic_weight)

    def clone_for_graph_move(self):
        return MachineOutgoingEdgePartition(
            self._identifier, self._pre_vertex, self._label)
