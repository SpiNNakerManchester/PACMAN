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
from pacman.model.graphs.machine import MachineEdge
from pacman.utilities.algorithm_utilities\
    .partition_algorithm_utilities import (
        get_multidimensional_slices, get_remaining_constraints)

logger = FormatAdapter(logging.getLogger(__name__))


class SplitterFixedLegacy(AbstractSplitterCommon):

    __slots__ = ["__slices", "__vertex_map", "__max_atoms"]

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

    SPLITTER_NAME = "SplitterFixedLegacy"

    def __init__(self, splitter_name=None):
        if splitter_name is None:
            splitter_name = self.SPLITTER_NAME
        super().__init__(splitter_name)
        self.__vertex_map = None
        self.__slices = None
        self.__max_atoms = None

    @overrides(AbstractSplitterCommon.set_governed_app_vertex)
    def set_governed_app_vertex(self, app_vertex):
        super().set_governed_app_vertex(app_vertex)
        if not isinstance(app_vertex, LegacyPartitionerAPI):
            for abstractmethod in LegacyPartitionerAPI._abstract_methods():
                check = getattr(app_vertex, abstractmethod, None)
                if not check:
                    raise PacmanConfigurationException(
                        self.NOT_SUITABLE_VERTEX_ERROR.format(
                            app_vertex.label, self._splitter_name,
                            abstractmethod))
                logger.warning(self.NOT_API_WARNING)

    @overrides(AbstractSplitterCommon.get_out_going_vertices)
    def get_out_going_vertices(self, edge, outgoing_edge_partition):
        return self.__all_vertex_map

    @overrides(AbstractSplitterCommon.get_in_coming_vertices)
    def get_in_coming_vertices(
            self, edge, outgoing_edge_partition, src_machine_vertex):
        return self.__all_vertex_map

    @overrides(AbstractSplitterCommon.machine_vertices_for_recording)
    def machine_vertices_for_recording(self, variable_to_record):
        return list(self._governed_app_vertex.machine_vertices)

    @property
    def __all_vertex_map(self):
        if self.__vertex_map is None:
            self.__vertex_map = self._get_map([MachineEdge])
        return self.__vertex_map

    @overrides(AbstractSplitterCommon.get_out_going_slices)
    def get_out_going_slices(self):
        return self.__fixed_slices, True

    @overrides(AbstractSplitterCommon.get_in_coming_slices)
    def get_in_coming_slices(self):
        return self.__fixed_slices, True

    @overrides(AbstractSplitterCommon.set_max_atoms_per_core)
    def set_max_atoms_per_core(self, max_atoms_per_core, is_fixed_atoms):
        n_atoms = self._governed_app_vertex.atoms_shape

        if self.__max_atoms is None:
            self.__max_atoms = list(n_atoms)
        if isinstance(max_atoms_per_core, int):
            for i in range(len(self.__max_atoms)):
                self.__max_atoms[i] = min(
                    self.__max_atoms[i], max_atoms_per_core)
        else:
            if len(max_atoms_per_core) != len(n_atoms):
                raise PacmanConfigurationException(
                    "The length of max_atoms_per_core does not match the "
                    " number of dimensions")
            for i in range(len(self.__max_atoms)):
                self.__max_atoms[i] = min(
                    self.__max_atoms[i], max_atoms_per_core[i])

    @property
    def __fixed_slices(self):
        if self.__slices is None:
            n_atoms = self._governed_app_vertex.atoms_shape
            self.__slices = get_multidimensional_slices(
                n_atoms, self.__max_atoms)
        return self.__slices

    @overrides(AbstractSplitterCommon.create_machine_vertices)
    def create_machine_vertices(self, resource_tracker, machine_graph):
        app_vertex = self._governed_app_vertex
        remaining_constraints = get_remaining_constraints(app_vertex)
        for vertex_slice in self.__fixed_slices:
            resources = app_vertex.get_resources_used_by_atoms(vertex_slice)
            resource_tracker.allocate_constrained_resources(
                resources, remaining_constraints)
            label = f"MachineVertex for {vertex_slice} of {app_vertex.label}"
            machine_graph.add_vertex(app_vertex.create_machine_vertex(
                vertex_slice, resources, label, remaining_constraints))

    @overrides(AbstractSplitterCommon.reset_called)
    def reset_called(self):
        self.__slices = None
        self.__vertex_map = None
