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
from pacman.model.graphs.abstract_single_source_partition import \
    AbstractSingleSourcePartition
from spinn_utilities.abstract_base import abstractmethod

_REPR_TEMPLATE = \
    "OutgoingEdgePartition(identifier={}, edges={}, constraints={}, label={})"


class OutgoingEdgePartition(AbstractSingleSourcePartition):
    """ A collection of edges which start at a single vertex which have the
        same semantics and so can share a single key.
    """

    __slots__ = []

    def __init__(
            self, identifier, allowed_edge_types, pre_vertex, traffic_type,
            constraints=None, label=None, traffic_weight=1):
        """
        :param identifier: The identifier of the partition
        :param allowed_edge_types: The types of edges allowed
        :param constraints: Any initial constraints
        :param label: An optional label of the partition
        :param traffic_weight: The weight of traffic going down this partition
        """
        AbstractSingleSourcePartition.__init__(
            self, pre_vertex, identifier, allowed_edge_types, constraints,
            label, traffic_weight, "OutgoingEdgePartition",
            traffic_type=traffic_type)

    @abstractmethod
    def clone_for_graph_move(self):
        """ handle cloning this partition for moving between graphs.

        :return: a clone of this partition with no edge data
        """
