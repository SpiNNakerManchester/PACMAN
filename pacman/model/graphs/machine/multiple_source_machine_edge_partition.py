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
    AbstractEdgePartition, AbstractMultiplePartition)
from pacman.model.graphs.machine.machine_edge import MachineEdge


class MultipleSourceMachineEdgePartition(
        AbstractMachineEdgePartition, AbstractMultiplePartition):
    """ A simple implementation of a machine edge partition that will \
        communicate with SpiNNaker multicast packets. They have a common set \
        of sources with the same semantics and so can share a single key.
    """

    __slots__ = (
        "_traffic_type"
    )

    def __init__(
            self, pre_vertices, identifier, constraints=None, label=None,
            traffic_weight=1):
        """
        :param pre_vertices: the pre vertices
        :type pre_vertices: iterable (MachineVertex)
        :param str identifier: The identifier of the partition
        :param list(AbstractConstraint) constraints: Any initial constraints
        :param str label: An optional label of the partition
        :param int traffic_weight:
            The weight of traffic going down this partition
        """
        super(MultipleSourceMachineEdgePartition, self).__init__(
            pre_vertices=pre_vertices, identifier=identifier,
            allowed_edge_types=MachineEdge, constraints=constraints,
            label=label, traffic_weight=traffic_weight,
            class_name="MultipleMachineEdgePartition")
        self._traffic_type = EdgeTrafficType.MULTICAST

    @overrides(AbstractMultiplePartition.add_edge)
    def add_edge(self, edge):
        """ Add an edge to the edge partition.

        :param AbstractEdge edge: the edge to add
        :raises PacmanInvalidParameterException:
            If the edge does not belong in this edge partition
        """
        # Check for an incompatible traffic type
        AbstractMachineEdgePartition.check_edge(self, edge)
        AbstractMultiplePartition.add_edge(self, edge)

    @property
    @overrides(AbstractMachineEdgePartition.traffic_type)
    def traffic_type(self):
        """ The traffic type of all the edges in this edge partition.

        :rtype: EdgeTrafficType
        """
        return self._traffic_type

    @overrides(AbstractEdgePartition.clone_for_graph_move)
    def clone_for_graph_move(self):
        """
        :rtype: MultipleSourceMachineEdgePartition
        """
        return MultipleSourceMachineEdgePartition(
            self._pre_vertices, self._identifier, self._constraints,
            self._label, self._traffic_weight)
