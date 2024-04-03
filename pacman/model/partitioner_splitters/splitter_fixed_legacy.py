# Copyright (c) 2017 The University of Manchester
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
from typing import cast, Generic, List, Optional

from spinn_utilities.overrides import overrides
from spinn_utilities.log import FormatAdapter

from pacman.exceptions import PacmanConfigurationException
from pacman.model.partitioner_interfaces import LegacyPartitionerAPI
from pacman.utilities.algorithm_utilities.partition_algorithm_utilities import\
    get_multidimensional_slices
from pacman.model.graphs.machine import MachineVertex
from pacman.model.graphs.common import Slice
from pacman.utilities.utility_objs import ChipCounter

from .abstract_splitter_common import AbstractSplitterCommon, V


logger = FormatAdapter(logging.getLogger(__name__))


class SplitterFixedLegacy(AbstractSplitterCommon[V], Generic[V]):
    """
    Splitter for old-style vertices.

    .. note::
        Only to be used with :py:class:`ApplicationVertex` objects that also
        implement :py:class:`LegacyPartitionerAPI`.
    """

    __slots__ = ["__slices"]

    def __init__(self) -> None:
        super().__init__()
        self.__slices: Optional[List[Slice]] = None

    @overrides(AbstractSplitterCommon.set_governed_app_vertex)
    def set_governed_app_vertex(self, app_vertex: V):
        if not isinstance(app_vertex, LegacyPartitionerAPI):
            raise PacmanConfigurationException(
                f"{self} is not a LegacyPartitionerAPI")
        super().set_governed_app_vertex(app_vertex)

    @overrides(AbstractSplitterCommon.get_out_going_vertices)
    def get_out_going_vertices(self, partition_id: str) -> List[MachineVertex]:
        return list(self.governed_app_vertex.machine_vertices)

    @overrides(AbstractSplitterCommon.get_in_coming_vertices)
    def get_in_coming_vertices(self, partition_id: str) -> List[MachineVertex]:
        return list(self.governed_app_vertex.machine_vertices)

    @overrides(AbstractSplitterCommon.machine_vertices_for_recording)
    def machine_vertices_for_recording(
            self, variable_to_record: str) -> List[MachineVertex]:
        return list(self.governed_app_vertex.machine_vertices)

    @overrides(AbstractSplitterCommon.get_out_going_slices)
    def get_out_going_slices(self) -> List[Slice]:
        return self.__fixed_slices

    @overrides(AbstractSplitterCommon.get_in_coming_slices)
    def get_in_coming_slices(self) -> List[Slice]:
        return self.__fixed_slices

    @property
    def __fixed_slices(self) -> List[Slice]:
        if self.__slices is None:
            self.__slices = get_multidimensional_slices(
                self.governed_app_vertex)
        return self.__slices

    @overrides(AbstractSplitterCommon.create_machine_vertices)
    def create_machine_vertices(self, chip_counter: ChipCounter):
        app_vertex = self.governed_app_vertex
        # The mypy needs to know the vertex implements LegacyPartitionerAPI
        # We know is does because we checked when setting
        lp = cast(LegacyPartitionerAPI, app_vertex)

        for vertex_slice in self.__fixed_slices:
            sdram = lp.get_sdram_used_by_atoms(vertex_slice)
            chip_counter.add_core(sdram)
            label = f"{app_vertex.label}{vertex_slice}"
            machine_vertex = lp.create_machine_vertex(vertex_slice, sdram, label)
            app_vertex.remember_machine_vertex(machine_vertex)

    @overrides(AbstractSplitterCommon.reset_called)
    def reset_called(self) -> None:
        self.__slices = None
