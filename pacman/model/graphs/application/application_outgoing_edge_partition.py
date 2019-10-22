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
from pacman.model.graphs.machine import MachineOutgoingEdgePartition
from spinn_utilities.overrides import overrides
from .application_edge import ApplicationEdge
from pacman.model.graphs.impl import OutgoingEdgePartition


class ApplicationOutgoingEdgePartition(OutgoingEdgePartition):
    """ Edge partition for the application graph.
    """

    __slots__ = ()

    def __init__(self, identifier, pre_vertex, constraints=None, label=None):
        super(ApplicationOutgoingEdgePartition, self).__init__(
            identifier, ApplicationEdge, pre_vertex, constraints, label)

    def convert_to_machine_out_going_partition(self, machine_pre_vertex):
        return MachineOutgoingEdgePartition(
            identifier=self._identifier, pre_vertex=machine_pre_vertex,
            constraints=self._constraints)

    @overrides(OutgoingEdgePartition.clone_for_graph_move)
    def clone_for_graph_move(self):
        return ApplicationOutgoingEdgePartition(
            self._identifier, self._pre_vertex, self._label)
