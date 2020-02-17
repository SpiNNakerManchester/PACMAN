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
from pacman.model.graphs.common import EdgeTrafficType
from pacman.model.graphs.impl import OutgoingEdgePartition
from .machine_edge import MachineEdge


class MachineOutgoingEdgePartition(OutgoingEdgePartition):
    """ An outgoing edge partition for a Machine Graph.
    """

    __slots__ = []

    def __init__(self, identifier, pre_vertex, constraints=None, label=None,
                 traffic_weight=1, traffic_type=EdgeTrafficType.MULTICAST):
        """
        :param identifier: The identifier of the partition
        :param constraints: Any initial constraints
        :param pre_vertex: the pre vertex for this partition
        :param label: An optional label of the partition
        :param traffic_weight: the weight of this partition in relation\
            to other partitions
        """
        OutgoingEdgePartition.__init__(
            self, identifier=identifier, allowed_edge_types=MachineEdge,
            pre_vertex=pre_vertex, traffic_type=traffic_type,
            constraints=constraints, label=label,
            traffic_weight=traffic_weight)

    def clone_for_graph_move(self):
        return MachineOutgoingEdgePartition(
            identifier=self._identifier, pre_vertex=self._pre_vertex,
            constraints=list(self._constraints), label=self._label,
            traffic_weight=self._traffic_weight,
            traffic_type=self._traffic_type)
