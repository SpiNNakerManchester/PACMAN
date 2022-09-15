# Copyright (c) 2021 The University of Manchester
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

from pacman.model.partitioner_splitters.abstract_splitters import (
    AbstractSplitterCommon)
from spinn_utilities.overrides import overrides
from pacman.model.graphs.application import (
    ApplicationFPGAVertex, ApplicationSpiNNakerLinkVertex)
from pacman.model.graphs.machine import (
    MachineFPGAVertex, MachineSpiNNakerLinkVertex)
from pacman.exceptions import PacmanConfigurationException,\
    PacmanNotExistException


class SplitterExternalDevice(AbstractSplitterCommon):

    __slots__ = [
        # Machine vertices that will send packets into the network
        "__incoming_vertices",
        # Machine vertices that will receive packets from the network
        "__outgoing_vertex",
        # Slices of incoming vertices (not exactly but hopefully close enough)
        "__incoming_slices",
        # Slice of outgoing vertex (which really doesn't matter here)
        "__outgoing_slice"
    ]

    @overrides(AbstractSplitterCommon.set_governed_app_vertex)
    def set_governed_app_vertex(self, app_vertex):
        super(SplitterExternalDevice, self).set_governed_app_vertex(app_vertex)

        self.__incoming_vertices = list()
        self.__incoming_slices = list()
        self.__outgoing_vertex = None
        self.__outgoing_slice = None

        if isinstance(app_vertex, ApplicationFPGAVertex):
            # This can have multiple FPGA connections per board
            for fpga in app_vertex.incoming_fpga_connections:
                for i in range(app_vertex.n_machine_vertices_per_link):
                    label = (
                        f"Incoming Machine vertex {i} for"
                        f" {app_vertex.label}"
                        f":{fpga.fpga_id}:{fpga.fpga_link_id}"
                        f":{fpga.board_address}:{fpga.chip_coords}")
                    vertex_slice = app_vertex.get_incoming_slice_for_link(
                        fpga, i)
                    vertex = MachineFPGAVertex(
                        fpga.fpga_id, fpga.fpga_link_id,
                        fpga.board_address, fpga.chip_coords, label=label,
                        app_vertex=app_vertex, vertex_slice=vertex_slice,
                        incoming=True, outgoing=False)
                    self.__incoming_vertices.append(vertex)
                    self.__incoming_slices.append(vertex_slice)
            fpga = app_vertex.outgoing_fpga_connection
            if fpga is not None:
                label = (
                    f"Outgoing Machine vertex for {app_vertex.label}"
                    f":{fpga.fpga_id}:{fpga.fpga_link_id}"
                    f":{fpga.board_address}:{fpga.chip_coords}")
                vertex_slice = app_vertex.get_outgoing_slice()
                vertex = MachineFPGAVertex(
                    fpga.fpga_id, fpga.fpga_link_id, fpga.board_address,
                    fpga.chip_coords, app_vertex=app_vertex, label=label,
                    vertex_slice=vertex_slice, incoming=False, outgoing=True)
                self.__outgoing_vertex = vertex
                self.__outgoing_slice = vertex_slice

        elif isinstance(app_vertex, ApplicationSpiNNakerLinkVertex):
            # So far this only handles one connection in total
            label = f"Machine vertex for {app_vertex.label}"

            if app_vertex.incoming:
                for i in range(app_vertex.n_machine_vertices):
                    vertex_slice = app_vertex.get_incoming_slice(i)
                    vertex = MachineSpiNNakerLinkVertex(
                        app_vertex.spinnaker_link_id, app_vertex.board_address,
                        None, label=label, app_vertex=app_vertex,
                        vertex_slice=vertex_slice, incoming=True,
                        outgoing=False)
                    self.__incoming_vertices.append(vertex)
                    self.__incoming_slices.append(vertex_slice)
            if app_vertex.outgoing:
                self.__outgoing_slice = app_vertex.get_outgoing_slice()
                self.__outgoing_vertex = MachineSpiNNakerLinkVertex(
                    app_vertex.spinnaker_link_id, app_vertex.board_address,
                    None, label=label, app_vertex=app_vertex,
                    vertex_slice=self.__outgoing_slice, incoming=False,
                    outgoing=True)
        else:
            raise PacmanConfigurationException(
                f"Unknown vertex type to splitter: {app_vertex}")

    @overrides(AbstractSplitterCommon.create_machine_vertices)
    def create_machine_vertices(self, chip_counter):
        app_vertex = self._governed_app_vertex
        for vertex in self.__incoming_vertices:
            # machine_graph.add_vertex(vertex)
            chip_counter.add_core(vertex.sdram_required)
            app_vertex.remember_machine_vertex(vertex)
        if self.__outgoing_vertex is not None:
            # machine_graph.add_vertex(self.__outgoing_vertex)
            chip_counter.add_core(self.__outgoing_vertex.sdram_required)
            app_vertex.remember_machine_vertex(self.__outgoing_vertex)

    @overrides(AbstractSplitterCommon.get_in_coming_slices)
    def get_in_coming_slices(self):
        if self.__outgoing_vertex is None:
            return []
        return [self.__outgoing_slice]

    @overrides(AbstractSplitterCommon.get_out_going_slices)
    def get_out_going_slices(self):
        return self.__incoming_slices

    @overrides(AbstractSplitterCommon.get_in_coming_vertices)
    def get_in_coming_vertices(self, partition_id):
        # Note, the incoming vertex is how to get packets into this device,
        # so we want to direct it at the outgoing vertex!
        if self.__outgoing_vertex is None:
            raise PacmanNotExistException(
                f"The target device of {self} doesn't support outgoing"
                " traffic")
        return [self.__outgoing_vertex]

    @overrides(AbstractSplitterCommon.get_out_going_vertices)
    def get_out_going_vertices(self, partition_id):
        # Note, the outgoing vertex is how to get packets out of this device,
        # so we want to direct it at the incoming vertices!
        if not self.__incoming_vertices:
            raise PacmanNotExistException(
                f"The target device of {self} doesn't support incoming"
                " traffic")
        return self.__incoming_vertices

    @overrides(AbstractSplitterCommon.machine_vertices_for_recording)
    def machine_vertices_for_recording(self, variable_to_record):
        return []

    @overrides(AbstractSplitterCommon.reset_called)
    def reset_called(self):
        pass
