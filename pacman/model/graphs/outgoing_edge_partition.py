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
from pacman.model.graphs import AbstractEdgePartition
from .abstract_single_source_partition import AbstractSingleSourcePartition


class OutgoingEdgePartition(AbstractSingleSourcePartition):
    """ A collection of edges which start at a single vertex which have the \
        same semantics. The traffic type and allowed edge type(s) must be \
        specified.
    """

    __slots__ = ()

    def __init__(
            self, identifier, allowed_edge_types, pre_vertex,
            traffic_type, constraints=None, label=None, traffic_weight=1):
        """
        :param str identifier: The identifier of the partition
        :param allowed_edge_types: The types of edges allowed
        :type allowed_edge_types: type or tuple(type, ...)
        :param AbstractVertex pre_vertex: The source of this partition
        :param EdgeTrafficType traffic_type:
            What kind of traffic will be carried by this partition
        :param list(AbstractConstraint) constraints: Any initial constraints
        :param str label: An optional label of the partition
        :param int traffic_weight:
            The weight of traffic going down this partition
        """
        super(OutgoingEdgePartition, self).__init__(
            pre_vertex=pre_vertex, identifier=identifier,
            allowed_edge_types=allowed_edge_types, constraints=constraints,
            label=label, traffic_weight=traffic_weight,
            class_name="OutgoingEdgePartition", traffic_type=traffic_type)

    @overrides(AbstractEdgePartition.clone_for_graph_move)
    def clone_for_graph_move(self):
        """
        :rtype: OutgoingEdgePartition
        """
        return OutgoingEdgePartition(
            self._identifier, self._allowed_edge_types, self._pre_vertex,
            self._traffic_type, self._constraints, self._label,
            self._traffic_weight)
