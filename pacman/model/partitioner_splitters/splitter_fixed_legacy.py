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
import logging
from pacman.exceptions import PacmanConfigurationException
from pacman.model.partitioner_interfaces import LegacyPartitionerAPI
from pacman.model.partitioner_splitters.abstract_splitters import (
    AbstractSplitterCommon)
from spinn_utilities.overrides import overrides
from spinn_utilities.log import FormatAdapter
from pacman.utilities.algorithm_utilities\
    .partition_algorithm_utilities import get_multidimensional_slices

logger = FormatAdapter(logging.getLogger(__name__))


class SplitterFixedLegacy(AbstractSplitterCommon):

    __slots__ = ["__slices"]

    def __init__(self, splitter_name=None):
        super().__init__()
        self.__slices = None

    @overrides(AbstractSplitterCommon.set_governed_app_vertex)
    def set_governed_app_vertex(self, app_vertex):
        if not isinstance(app_vertex, LegacyPartitionerAPI):
            raise PacmanConfigurationException(
                f"{self} is not a LegacyPartitionerAPI")
        super().set_governed_app_vertex(app_vertex)

    @overrides(AbstractSplitterCommon.get_out_going_vertices)
    def get_out_going_vertices(self, partition_id):
        return list(self._governed_app_vertex.machine_vertices)

    @overrides(AbstractSplitterCommon.get_in_coming_vertices)
    def get_in_coming_vertices(self, partition_id):
        return list(self._governed_app_vertex.machine_vertices)

    @overrides(AbstractSplitterCommon.machine_vertices_for_recording)
    def machine_vertices_for_recording(self, variable_to_record):
        return list(self._governed_app_vertex.machine_vertices)

    @overrides(AbstractSplitterCommon.get_out_going_slices)
    def get_out_going_slices(self):
        return self.__fixed_slices

    @overrides(AbstractSplitterCommon.get_in_coming_slices)
    def get_in_coming_slices(self):
        return self.__fixed_slices

    @property
    def __fixed_slices(self):
        if self.__slices is None:
            self.__slices = get_multidimensional_slices(
                self._governed_app_vertex)
        return self.__slices

    @overrides(AbstractSplitterCommon.create_machine_vertices)
    def create_machine_vertices(self, chip_counter):
        app_vertex = self._governed_app_vertex
        for vertex_slice in self.__fixed_slices:
            sdram = app_vertex.get_sdram_used_by_atoms(vertex_slice)
            chip_counter.add_core(sdram)
            label = f"{app_vertex.label}{vertex_slice}"
            machine_vertex = app_vertex.create_machine_vertex(
                vertex_slice, sdram, label)
            app_vertex.remember_machine_vertex(machine_vertex)

    @overrides(AbstractSplitterCommon.reset_called)
    def reset_called(self):
        self.__slices = None
