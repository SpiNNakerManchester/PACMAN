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

from dataclasses import dataclass
import logging
from typing import List, Optional
from spinn_utilities.overrides import overrides
from spinn_utilities.log import FormatAdapter
from pacman.exceptions import PacmanConfigurationException
from pacman.model.graphs.common import Slice
from pacman.model.partitioner_interfaces import LegacyPartitionerAPI
from .abstract_splitter_common import AbstractSplitterCommon
from pacman.model.graphs.application import ApplicationVertex
from pacman.model.graphs.machine import MachineVertex
from pacman.utilities.utility_objs.chip_counter import ChipCounter
from pacman.model.resources import AbstractSDRAM

logger = FormatAdapter(logging.getLogger(__name__))


@dataclass(frozen=True)
class _State:
    vertex: MachineVertex
    vertex_slice: Slice
    sdram: AbstractSDRAM


class SplitterOneToOneLegacy(AbstractSplitterCommon[ApplicationVertex]):
    """
    A one-to-one splitter for legacy vertices.
    """

    __slots__ = ("__state", )

    def __init__(self) -> None:
        super().__init__()
        self.__state: Optional[_State] = None

    @property
    def _state(self) -> _State:
        assert self.__state is not None, "no app vertex set"
        return self.__state

    @overrides(AbstractSplitterCommon.set_governed_app_vertex)
    def set_governed_app_vertex(self, app_vertex: ApplicationVertex):
        if not isinstance(app_vertex, LegacyPartitionerAPI):
            raise PacmanConfigurationException(
                f"{self} is not a LegacyPartitionerAPI")
        super().set_governed_app_vertex(app_vertex)
        _slice = Slice(0, app_vertex.n_atoms - 1)
        sdram = app_vertex.get_sdram_used_by_atoms(_slice)
        self.__state = _State(
            app_vertex.create_machine_vertex(
                vertex_slice=_slice, sdram=sdram, label=None),
            _slice, sdram)
        app_vertex.remember_machine_vertex(self._state.vertex)

    @overrides(AbstractSplitterCommon.create_machine_vertices)
    def create_machine_vertices(self, chip_counter: ChipCounter):
        chip_counter.add_core(self._state.sdram)

    @overrides(AbstractSplitterCommon.get_out_going_slices)
    def get_out_going_slices(self) -> List[Slice]:
        return [self._state.vertex_slice]

    @overrides(AbstractSplitterCommon.get_in_coming_slices)
    def get_in_coming_slices(self) -> List[Slice]:
        return [self._state.vertex_slice]

    @overrides(AbstractSplitterCommon.get_out_going_vertices)
    def get_out_going_vertices(self, partition_id: str) -> List[MachineVertex]:
        return [self._state.vertex]

    @overrides(AbstractSplitterCommon.get_in_coming_vertices)
    def get_in_coming_vertices(self, partition_id: str) -> List[MachineVertex]:
        return [self._state.vertex]

    @overrides(AbstractSplitterCommon.machine_vertices_for_recording)
    def machine_vertices_for_recording(
            self, variable_to_record: str) -> List[MachineVertex]:
        return [self._state.vertex]

    @overrides(AbstractSplitterCommon.reset_called)
    def reset_called(self) -> None:
        pass
