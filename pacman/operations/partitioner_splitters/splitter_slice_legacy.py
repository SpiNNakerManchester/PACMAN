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
from pacman.exceptions import PacmanConfigurationException
from pacman.model.partitioner_interfaces.abstract_splitter_common import (
    AbstractSplitterCommon)
from pacman.model.partitioner_interfaces.legacy_partitioner_api import (
    LegacyPartitionerAPI)
from spinn_utilities.overrides import overrides


class SplitterSliceLegacy(AbstractSplitterCommon):

    __slots__ = []

    NOT_SUITABLE_VERTEX_ERROR = (
        "The vertex {} cannot be supported by the SplitterSliceLegacy as"
        " the vertex does not support the required API of "
        "LegacyPartitionerAPI. Please inherit from the class in "
        "pacman.model.partitioner_interfaces.legacy_partitioner_api and try "
        "again.")

    STR_MESSAGE = "SplitterSliceLegacy governing app vertex {}"

    def __init__(self):
        AbstractSplitterCommon.__init__(self)

    def __str__(self):
        return self.STR_MESSAGE.format(self._governed_app_vertex)

    def __repr__(self):
        return self.__str__()

    @overrides(AbstractSplitterCommon.set_governed_app_vertex)
    def set_governed_app_vertex(self, app_vertex):
        AbstractSplitterCommon.set_governed_app_vertex(self, app_vertex)
        if not isinstance(app_vertex, LegacyPartitionerAPI):
            raise PacmanConfigurationException(
                self.NOT_SUITABLE_VERTEX_ERROR.format(app_vertex.label))

    def __split(self, resource_tracker, machine_graph):
        """ TODO NEEDS FILLING IN. STEAL FROM PARTITION AND PLACE"""

    @overrides(AbstractSplitterCommon.create_machine_vertices)
    def create_machine_vertices(self, resource_tracker, machine_graph):
        slices_resources_map = self.__split(resource_tracker, machine_graph)
        for vertex_slice in slices_resources_map:
            machine_vertex = self._governed_app_vertex.create_machine_vertex(
                vertex_slice, slices_resources_map[vertex_slice])
            machine_graph.add_vertex(machine_vertex)
        return True

    @overrides(AbstractSplitterCommon.get_out_going_slices)
    def get_out_going_slices(self):
        return self._governed_app_vertex.vertex_slices

    @overrides(AbstractSplitterCommon.get_in_coming_slices)
    def get_in_coming_slices(self):
        return self._governed_app_vertex.vertex_slices

    @overrides(AbstractSplitterCommon.get_pre_vertices)
    def get_pre_vertices(self, edge, outgoing_edge_partition):
        return self._governed_app_vertex.machine_vertices

    @overrides(AbstractSplitterCommon.get_post_vertices)
    def get_post_vertices(
            self, edge, outgoing_edge_partition, src_machine_vertex):
        return self._governed_app_vertex.machine_vertices

    @overrides(AbstractSplitterCommon.machine_vertices_for_recording)
    def machine_vertices_for_recording(self, variable_to_record):
        return self._governed_app_vertex.machine_vertices
