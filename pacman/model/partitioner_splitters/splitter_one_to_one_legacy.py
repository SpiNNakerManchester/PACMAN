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
from typing import cast, List, Optional
from spinn_utilities.overrides import overrides
from spinn_utilities.log import FormatAdapter
from pacman.exceptions import PacmanConfigurationException
from pacman.model.graphs.application import ApplicationVertex
from pacman.model.graphs.common import Slice
from pacman.model.graphs.machine import MachineVertex
from pacman.model.partitioner_interfaces import LegacyPartitionerAPI
from pacman.model.resources import AbstractSDRAM
from pacman.utilities.utility_objs import ChipCounter
from .abstract_splitter_common import AbstractSplitterCommon

logger = FormatAdapter(logging.getLogger(__name__))


class SplitterOneToOneLegacy(AbstractSplitterCommon[ApplicationVertex]):
    """
    A Splitter which hands an vertex with the LegacyPartitionerAPI

    The assumption is that each ApplicationVertex
    will get just one Machine vertex
    """

    __slots__ = [
        "_machine_vertex",
        "_vertex_slice",
        "_sdram"]

    def __init__(self) -> None:
        super().__init__()
        self._machine_vertex: Optional[MachineVertex] = None
        self._vertex_slice: Optional[Slice] = None
        self._sdram: Optional[AbstractSDRAM] = None

    @overrides(AbstractSplitterCommon.set_governed_app_vertex)
    def set_governed_app_vertex(self, app_vertex: ApplicationVertex):
        if not isinstance(app_vertex, LegacyPartitionerAPI):
            raise PacmanConfigurationException(
                f"{self} is not a LegacyPartitionerAPI")
        super().set_governed_app_vertex(app_vertex)
        self._vertex_slice = Slice(0, self.governed_app_vertex.n_atoms - 1)
        lp = cast(LegacyPartitionerAPI, app_vertex)
        self._sdram = lp.get_sdram_used_by_atoms(
            self._vertex_slice)
        self._machine_vertex = lp.create_machine_vertex(
            vertex_slice=self._vertex_slice,
            sdram=self._sdram, label=None)
        self.governed_app_vertex.remember_machine_vertex(self._machine_vertex)

    @overrides(AbstractSplitterCommon.create_machine_vertices)
    def create_machine_vertices(self, chip_counter: ChipCounter):
        assert self._sdram is not None
        chip_counter.add_core(self._sdram)

    @overrides(AbstractSplitterCommon.get_out_going_slices)
    def get_out_going_slices(self) -> List[Slice]:
        assert self._vertex_slice is not None
        return [self._vertex_slice]

    @overrides(AbstractSplitterCommon.get_in_coming_slices)
    def get_in_coming_slices(self) -> List[Slice]:
        assert self._vertex_slice is not None
        return [self._vertex_slice]

    @overrides(AbstractSplitterCommon.get_out_going_vertices)
    def get_out_going_vertices(self, partition_id: str) -> List[MachineVertex]:
        assert self._machine_vertex is not None
        return [self._machine_vertex]

    @overrides(AbstractSplitterCommon.get_in_coming_vertices)
    def get_in_coming_vertices(self, partition_id: str) -> List[MachineVertex]:
        assert self._machine_vertex is not None
        return [self._machine_vertex]

    @overrides(AbstractSplitterCommon.machine_vertices_for_recording)
    def machine_vertices_for_recording(
            self, variable_to_record: str) -> List[MachineVertex]:
        assert self._machine_vertex is not None
        return [self._machine_vertex]

    @overrides(AbstractSplitterCommon.reset_called)
    def reset_called(self) -> None:
        pass
