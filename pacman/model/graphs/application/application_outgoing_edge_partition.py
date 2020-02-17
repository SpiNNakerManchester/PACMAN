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
from pacman.model.graphs.abstract_application_outgoing_partition import \
    AbstractApplicationOutgoingPartition
from pacman.model.graphs.common import EdgeTrafficType
from pacman.model.graphs.machine import MachineOutgoingEdgePartition
from .application_edge import ApplicationEdge
from pacman.model.graphs.impl import OutgoingEdgePartition


class ApplicationOutgoingEdgePartition(
        OutgoingEdgePartition, AbstractApplicationOutgoingPartition):
    """ Edge partition for the application graph.
    """

    __slots__ = ()

    def __init__(
            self, identifier, pre_vertex,
            traffic_type=EdgeTrafficType.MULTICAST, constraints=None,
            label=None):
        OutgoingEdgePartition.__init__(
            self, identifier=identifier, allowed_edge_types=ApplicationEdge,
            pre_vertex=pre_vertex, traffic_type=traffic_type,
            constraints=constraints, label=label)
        AbstractApplicationOutgoingPartition.__init__(self)

    def convert_to_machine_out_going_partition(self, machine_pre_vertex):
        return MachineOutgoingEdgePartition(
            identifier=self._identifier, pre_vertex=machine_pre_vertex,
            constraints=self._constraints)

    def clone_for_graph_move(self):
        return ApplicationOutgoingEdgePartition(
            self._identifier, self._pre_vertex, self._label)
