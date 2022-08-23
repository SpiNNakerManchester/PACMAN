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
from pacman.model.graphs.common import Slice
from pacman.model.partitioner_splitters.abstract_splitters import (
    AbstractSplitterCommon)
from pacman.model.partitioner_interfaces import LegacyPartitionerAPI

logger = FormatAdapter(logging.getLogger(__name__))


class SplitterOneToOneLegacy(AbstractSplitterCommon):

    NOT_API_WARNING = (
        "Your vertex is deprecated. Please add a Splitter or "
        "inherit from the class in "
        "pacman.model.partitioner_interfaces.legacy_partitioner_api")

    NOT_SUITABLE_VERTEX_ERROR = (
        "The vertex {} cannot be supported by the {} as"
        " the vertex does not support the required method {} of "
        "LegacyPartitionerAPI. Please inherit from the class in "
        "pacman.model.partitioner_interfaces.legacy_partitioner_api and try "
        "again.")

    __slots__ = [
        "_machine_vertex",
        "_vertex_slice",
        "_sdram"]

    def __init__(self):
        super().__init__()
        self._machine_vertex = None
        self._vertex_slice = None
        self._sdram = None

    @overrides(AbstractSplitterCommon.set_governed_app_vertex)
    def set_governed_app_vertex(self, app_vertex):
        super().set_governed_app_vertex(app_vertex)
        self._vertex_slice = Slice(0, self._governed_app_vertex.n_atoms - 1)
        self._sdram = (
             self._governed_app_vertex.get_sdram_used_by_atoms(
                self._vertex_slice))
        self._machine_vertex = (
            self._governed_app_vertex.create_machine_vertex(
                vertex_slice=self._vertex_slice,
                sdram=self._sdram, label=None, constraints=None))
        self._governed_app_vertex.remember_machine_vertex(self._machine_vertex)
        if not isinstance(app_vertex, LegacyPartitionerAPI):
            for abstractmethod in LegacyPartitionerAPI.abstract_methods():
                check = getattr(app_vertex, abstractmethod, None)
                if not check:
                    raise PacmanConfigurationException(
                        self.NOT_SUITABLE_VERTEX_ERROR.format(
                            app_vertex.label, type(self).__name__,
                            abstractmethod))
                logger.warning(self.NOT_API_WARNING)

    @overrides(AbstractSplitterCommon.create_machine_vertices)
    def create_machine_vertices(self, chip_counter):
        chip_counter.add_core(self._sdram)

    @overrides(AbstractSplitterCommon.get_out_going_slices)
    def get_out_going_slices(self):
        return [self._vertex_slice]

    @overrides(AbstractSplitterCommon.get_in_coming_slices)
    def get_in_coming_slices(self):
        return [self._vertex_slice]

    @overrides(AbstractSplitterCommon.get_out_going_vertices)
    def get_out_going_vertices(self, partition_id):
        return [self._machine_vertex]

    @overrides(AbstractSplitterCommon.get_in_coming_vertices)
    def get_in_coming_vertices(self, partition_id):
        return [self._machine_vertex]

    @overrides(AbstractSplitterCommon.machine_vertices_for_recording)
    def machine_vertices_for_recording(self, variable_to_record):
        return [self._machine_vertex]

    @overrides(AbstractSplitterCommon.reset_called)
    def reset_called(self):
        pass
