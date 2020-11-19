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
from pacman.model.graphs.machine.abstract_machine_edge_partition import (
    AbstractMachineEdgePartition)
from spinn_utilities.overrides import overrides
from pacman.model.graphs.common import EdgeTrafficType
from pacman.model.graphs import (
    AbstractEdgePartition, AbstractSingleSourcePartition)
from pacman.model.graphs.machine.machine_edge import MachineEdge


class MulticastEdgePartition(
        AbstractSingleSourcePartition, AbstractMachineEdgePartition):
    """ A simple implementation of a machine edge partition that will \
        communicate with SpiNNaker multicast packets. They have a common set \
        of sources with the same semantics and so can share a single key.
    """

    __slots__ = ()

    def __init__(
            self, pre_vertex, identifier, constraints=None, label=None,
            traffic_weight=1):
        """
        :param str identifier: The identifier of the partition
        :param list(AbstractConstraint) constraints: Any initial constraints
        :param str label: An optional label of the partition
        :param int traffic_weight:
            The weight of traffic going down this partition
        """
        super(MulticastEdgePartition, self).__init__(
            pre_vertex=pre_vertex, identifier=identifier,
            allowed_edge_types=MachineEdge, constraints=constraints,
            label=label, traffic_weight=traffic_weight,
            class_name="SingleSourceMachineEdgePartition")

    @overrides(AbstractSingleSourcePartition.add_edge)
    def add_edge(self, edge):
        AbstractMachineEdgePartition.check_edge(self, edge)
        AbstractSingleSourcePartition.add_edge(self, edge)

    @property
    @overrides(AbstractMachineEdgePartition.traffic_type, extend_doc=False)
    def traffic_type(self):
        """ The traffic type of all the edges in this edge partition.

        :rtype: EdgeTrafficType
        """
        return EdgeTrafficType.MULTICAST

    @overrides(AbstractEdgePartition.clone_for_graph_move)
    def clone_for_graph_move(self):
        """
        :rtype: MulticastEdgePartition
        """
        return MulticastEdgePartition(
            self._pre_vertex, self._identifier, self._constraints,
            self._label, self._traffic_weight)
