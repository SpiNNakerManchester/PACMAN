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
    MachineFPGAVertex, MachineSpiNNakerLinkVertex, MachineEdge)
from pacman.exceptions import PacmanConfigurationException,\
    PacmanNotExistException
from pacman.model.graphs.common.slice import Slice
import math


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

    def __init__(self, splitter_name=None):
        super(SplitterExternalDevice, self).__init__(splitter_name)
        self.__incoming_slices = None
        self.__outgoing_slice = None

    @overrides(AbstractSplitterCommon.create_machine_vertices)
    def create_machine_vertices(self, resource_tracker, machine_graph):
        self.__incoming_vertices = list()
        self.__outgoing_vertex = None
        app_vertex = self._governed_app_vertex
        if isinstance(app_vertex, ApplicationFPGAVertex):
            # This can have multiple FPGA connections per board
            seen_incoming = dict()
            if app_vertex.incoming_fpga_connections:
                for fpga in app_vertex.incoming_fpga_connections:
                    label = (f"Machine vertex for {app_vertex.label}"
                             f":{fpga.fpga_id}:{fpga.fpga_link_id}"
                             f":{fpga.board_address}")
                    for _ in range(app_vertex.n_machine_vertices_per_link):
                        vertex = MachineFPGAVertex(
                            fpga.fpga_id, fpga.fpga_link_id,
                            fpga.board_address, label, app_vertex=app_vertex)
                        seen_incoming[fpga] = vertex
                        machine_graph.add_vertex(vertex)
                        self.__incoming_vertices.append(vertex)
            fpga = app_vertex.outgoing_fpga_connection
            if fpga is not None:
                if fpga in seen_incoming:
                    self.__outgoing_vertex = seen_incoming[fpga]
                else:
                    vertex = MachineFPGAVertex(
                        fpga.fpga_id, fpga.fpga_link_id, fpga.board_address)
                    machine_graph.add_vertex(vertex)
                    self.__outgoing_vertex = vertex

        elif isinstance(app_vertex, ApplicationSpiNNakerLinkVertex):
            # So far this only handles one connection in total
            label = f"Machine vertex for {app_vertex.label}"
            vertex = MachineSpiNNakerLinkVertex(
                app_vertex.spinnaker_link_id, app_vertex.board_address, label,
                app_vertex=app_vertex)
            machine_graph.add_vertex(vertex)
            self.__incoming_vertices = [vertex]
            self.__outgoing_vertex = vertex
        else:
            raise PacmanConfigurationException(
                f"Unknown vertex type to splitter: {app_vertex}")

    @overrides(AbstractSplitterCommon.get_in_coming_slices)
    def get_in_coming_slices(self):
        if self.__outgoing_vertex is None:
            return []
        if self.__outgoing_slice is None:
            # We actually don't care but hopefully this is OK...
            self.__outgoing_slice = Slice(0, self._governed_app_vertex.n_atoms)
        return [self.__outgoing_slice], True

    @overrides(AbstractSplitterCommon.get_out_going_slices)
    def get_out_going_slices(self):
        if self.__incoming_slices is not None:
            return self.__incoming_slices, True

        # This is a bit convoluted, since the slices are ill-defined here;
        # The number of slices will at least be correct though.
        app_vertex = self._governed_app_vertex
        fpga_conns = list(app_vertex.incoming_fpga_connections)
        v_per_link = app_vertex.n_machine_vertices_per_link
        atoms_per_slice = int(math.ceil(
            app_vertex.n_atoms / (len(fpga_conns) * v_per_link)))
        self.__incoming_slices = [Slice(0, atoms_per_slice)
                                  for _ in fpga_conns
                                  for _ in range(v_per_link)]
        return self.__incoming_slices, True

    @overrides(AbstractSplitterCommon.get_in_coming_vertices)
    def get_in_coming_vertices(
            self, edge, outgoing_edge_partition, src_machine_vertex):
        # Note, the incoming vertex is how to get packets into this device,
        # so we want to direct it at the outgoing vertex!
        if self.__outgoing_vertex is None:
            raise PacmanNotExistException(
                f"There is no way to reach the target device of {edge} via the"
                " FPGAs.  Please add an outgoing FPGA to the device.")
        return {self.__outgoing_vertex: [MachineEdge]}

    @overrides(AbstractSplitterCommon.get_out_going_vertices)
    def get_out_going_vertices(self, edge, outgoing_edge_partition):
        # Note, the outgoing vertex is how to get packets out of this device,
        # so we want to direct it at the incoming vertices!
        if not self.__incoming_vertices:
            raise PacmanNotExistException(
                f"There is no way for the target device of {edge} to send via"
                " the FPGAs.  Please add an incoming FPGA to the device.")
        return {v: [MachineEdge] for v in self.__incoming_vertices}

    @overrides(AbstractSplitterCommon.machine_vertices_for_recording)
    def machine_vertices_for_recording(self, variable_to_record):
        return []

    @overrides(AbstractSplitterCommon.reset_called)
    def reset_called(self):
        pass
