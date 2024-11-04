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
from typing import Generic, List, TypeVar
from spinn_utilities.overrides import overrides
from spinn_utilities.log import FormatAdapter
from pacman.exceptions import PacmanConfigurationException
from pacman.model.graphs.application.abstract import (
    AbstractOneAppOneMachineVertex)
from pacman.utilities.utility_objs import ChipCounter
from pacman.model.graphs.machine import MachineVertex
from pacman.model.graphs.common import Slice
from .abstract_splitter_common import AbstractSplitterCommon
#: :meta private:
MV = TypeVar("MV", bound=MachineVertex)
#: :meta private:
AV = TypeVar("AV", bound=AbstractOneAppOneMachineVertex)
logger = FormatAdapter(logging.getLogger(__name__))


class SplitterOneAppOneMachine(AbstractSplitterCommon[AV], Generic[AV, MV]):
    """
    Splitter that handles :py:class:`AbstractOneAppOneMachineVertex` vertices.
    """
    __slots__ = ()

    @overrides(AbstractSplitterCommon.set_governed_app_vertex)
    def set_governed_app_vertex(self, app_vertex: AV) -> None:
        if not isinstance(app_vertex, AbstractOneAppOneMachineVertex):
            raise PacmanConfigurationException(
                f"The vertex {app_vertex.label} cannot be supported by the "
                f"{type(self).__name__} as the vertex does not implement "
                "AbstractOneAppOneMachineVertex")
        super().set_governed_app_vertex(app_vertex)

    @overrides(AbstractSplitterCommon.create_machine_vertices)
    def create_machine_vertices(self, chip_counter: ChipCounter) -> None:
        chip_counter.add_core(
            self.governed_app_vertex.machine_vertex.sdram_required)

    @overrides(AbstractSplitterCommon.get_out_going_slices)
    def get_out_going_slices(self) -> List[Slice]:
        return [self.governed_app_vertex.machine_vertex.vertex_slice]

    @overrides(AbstractSplitterCommon.get_in_coming_slices)
    def get_in_coming_slices(self) -> List[Slice]:
        return [self.governed_app_vertex.machine_vertex.vertex_slice]

    @overrides(AbstractSplitterCommon.get_out_going_vertices)
    def get_out_going_vertices(self, partition_id: str) -> List[MV]:
        return [self.governed_app_vertex.machine_vertex]

    @overrides(AbstractSplitterCommon.get_in_coming_vertices)
    def get_in_coming_vertices(self, partition_id: str) -> List[MV]:
        return [self.governed_app_vertex.machine_vertex]

    @overrides(AbstractSplitterCommon.machine_vertices_for_recording)
    def machine_vertices_for_recording(
            self, variable_to_record: str) -> List[MV]:
        return [self.governed_app_vertex.machine_vertex]

    @overrides(AbstractSplitterCommon.reset_called)
    def reset_called(self) -> None:
        pass
