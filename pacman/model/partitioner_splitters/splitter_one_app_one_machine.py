# Copyright (c) 2020-2021 The University of Manchester
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

import logging
from spinn_utilities.overrides import overrides
from spinn_utilities.log import FormatAdapter
from pacman.exceptions import PacmanConfigurationException
from pacman.model.graphs.machine import MachineEdge
from pacman.model.partitioner_splitters.abstract_splitters import (
    AbstractSplitterCommon)
from pacman.model.graphs.application.abstract import (
    AbstractOneAppOneMachineVertex)

logger = FormatAdapter(logging.getLogger(__name__))


class SplitterOneAppOneMachine(AbstractSplitterCommon):

    NOT_SUITABLE_VERTEX_ERROR = (
        "The vertex {} cannot be supported by the {} as "
        "the vertex does not implement AbstractOneAppOneMachineVertex")

    __slots__ = []

    def __init__(self, splitter_name=None):
        if splitter_name is None:
            splitter_name = type(self).__name__
        super().__init__(splitter_name)

    def __repr__(self):
        return self.__str__()

    @overrides(AbstractSplitterCommon.set_governed_app_vertex)
    def set_governed_app_vertex(self, app_vertex):
        if not isinstance(app_vertex, AbstractOneAppOneMachineVertex):
            raise PacmanConfigurationException(
                self.NOT_SUITABLE_VERTEX_ERROR.format(
                    app_vertex.label, self._splitter_name))
        super().set_governed_app_vertex(app_vertex)

    @overrides(AbstractSplitterCommon.create_machine_vertices)
    def create_machine_vertices(self, resource_tracker, machine_graph):
        machine_vertex = self._governed_app_vertex.machine_vertex
        resource_tracker.allocate_constrained_resources(
            machine_vertex.resources_required, machine_vertex.constraints)
        machine_graph.add_vertex(machine_vertex)
        return machine_vertex

    @overrides(AbstractSplitterCommon.get_out_going_slices)
    def get_out_going_slices(self):
        return [self._governed_app_vertex.machine_vertex.vertex_slice], True

    @overrides(AbstractSplitterCommon.get_in_coming_slices)
    def get_in_coming_slices(self):
        return [self._governed_app_vertex.machine_vertex.vertex_slice], True

    @overrides(AbstractSplitterCommon.get_out_going_vertices)
    def get_out_going_vertices(self, edge, outgoing_edge_partition):
        return {self._governed_app_vertex.machine_vertex: [MachineEdge]}

    @overrides(AbstractSplitterCommon.get_in_coming_vertices)
    def get_in_coming_vertices(
            self, edge, outgoing_edge_partition, src_machine_vertex):
        return {self._governed_app_vertex.machine_vertex: [MachineEdge]}

    @overrides(AbstractSplitterCommon.machine_vertices_for_recording)
    def machine_vertices_for_recording(self, variable_to_record):
        return [self._governed_app_vertex.machine_vertex]

    @overrides(AbstractSplitterCommon.reset_called)
    def reset_called(self):
        pass
