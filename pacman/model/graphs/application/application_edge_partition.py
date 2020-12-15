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
from pacman.model.graphs import (
    AbstractEdgePartition, AbstractSingleSourcePartition)
from .application_edge import ApplicationEdge


class ApplicationEdgePartition(AbstractSingleSourcePartition):
    """ A simple implementation of an application edge partition that will\
        communicate using SpiNNaker multicast packets. They have the same \
        source(s) and semantics and so can share a single key.
    """

    __slots__ = ()

    def __init__(
            self, identifier, pre_vertex, constraints=None, label=None,
            traffic_weight=1):
        """
        :param str identifier: The identifier of the partition
        :param ApplicationVertex pre_vertex: The source of this partition
        :param list(AbstractConstraint) constraints: Any initial constraints
        :param str label: An optional label of the partition
        :param int traffic_weight:
            The weight of traffic going down this partition
        :param traffic_type: the traffic type acceptable here.
        """
        super(ApplicationEdgePartition, self).__init__(
            pre_vertex=pre_vertex, identifier=identifier,
            allowed_edge_types=ApplicationEdge, constraints=constraints,
            label=label, traffic_weight=traffic_weight,
            class_name="ApplicationEdgePartition")

    @overrides(AbstractEdgePartition.clone_without_edges)
    def clone_without_edges(self):
        """
        :rtype: ApplicationEdgePartition
        """
        return ApplicationEdgePartition(
            self._identifier, self._pre_vertex, self._constraints,
            self._label, self._traffic_weight)
