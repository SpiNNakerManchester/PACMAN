# Copyright (c) 2020 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from spinn_utilities.overrides import overrides
from spinn_utilities.log import FormatAdapter
from pacman.exceptions import PacmanConfigurationException
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

    @overrides(AbstractSplitterCommon.set_governed_app_vertex)
    def set_governed_app_vertex(self, app_vertex):
        if not isinstance(app_vertex, AbstractOneAppOneMachineVertex):
            raise PacmanConfigurationException(
                self.NOT_SUITABLE_VERTEX_ERROR.format(
                    app_vertex.label, type(self).__name__))
        super().set_governed_app_vertex(app_vertex)

    @overrides(AbstractSplitterCommon.create_machine_vertices)
    def create_machine_vertices(self, chip_counter):
        chip_counter.add_core(
            self._governed_app_vertex.machine_vertex.sdram_required)

    @overrides(AbstractSplitterCommon.get_out_going_slices)
    def get_out_going_slices(self):
        return [self._governed_app_vertex.machine_vertex.vertex_slice]

    @overrides(AbstractSplitterCommon.get_in_coming_slices)
    def get_in_coming_slices(self):
        return [self._governed_app_vertex.machine_vertex.vertex_slice]

    @overrides(AbstractSplitterCommon.get_out_going_vertices)
    def get_out_going_vertices(self, partition_id):
        return [self._governed_app_vertex.machine_vertex]

    @overrides(AbstractSplitterCommon.get_in_coming_vertices)
    def get_in_coming_vertices(self, partition_id):
        return [self._governed_app_vertex.machine_vertex]

    @overrides(AbstractSplitterCommon.machine_vertices_for_recording)
    def machine_vertices_for_recording(self, variable_to_record):
        return [self._governed_app_vertex.machine_vertex]

    @overrides(AbstractSplitterCommon.reset_called)
    def reset_called(self):
        pass
