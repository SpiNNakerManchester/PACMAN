from pacman.model.partitioner_splitters.abstract_splitters import (
    AbstractSplitterCommon)
from spinn_utilities.overrides import overrides
from pacman.model.graphs.application import (
    ApplicationFPGAVertex, ApplicationSpiNNakerLinkVertex)
from pacman.model.graphs.machine import (
    MachineFPGAVertex, MachineSpiNNakerLinkVertex, MachineEdge)
from pacman.exceptions import PacmanConfigurationException
from pacman.model.graphs.common.slice import Slice


class SplitterExternalDevice(AbstractSplitterCommon):

    __slots__ = [
        # Machine vertices that will send packets into the network
        "__incoming_vertices",
        # Machine vertices that will receive packets from the network
        "__outgoing_vertex"
    ]

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
                    vertex = MachineFPGAVertex(
                        fpga.fpga_id, fpga.fpga_link_id, fpga.board_address,
                        label, app_vertex=app_vertex)
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
            self.__incoming_vertices = [vertex]
            self.__outgoing_vertex = vertex
        else:
            raise PacmanConfigurationException(
                f"Unknown vertex type to splitter: {app_vertex}")

    @overrides(AbstractSplitterCommon.get_in_coming_slices)
    def get_in_coming_slices(self):
        return [Slice(0, self._governed_app_vertex.n_atoms)], True

    @overrides(AbstractSplitterCommon.get_out_going_slices)
    def get_out_going_slices(self):
        return [Slice(0, self._governed_app_vertex.n_atoms)], True

    @overrides(AbstractSplitterCommon.get_in_coming_vertices)
    def get_in_coming_vertices(
            self, edge, outgoing_edge_partition, src_machine_vertex):
        # Note, the incoming vertex is how to get packets into this device,
        # so we want to direct it at the outgoing vertex!
        if self.__outgoing_vertex is None:
            return {}
        return {self.__outgoing_vertex: [MachineEdge]}

    @overrides(AbstractSplitterCommon.get_out_going_vertices)
    def get_out_going_vertices(self, edge, outgoing_edge_partition):
        return {v: [MachineEdge] for v in self.__incoming_vertices}

    @overrides(AbstractSplitterCommon.machine_vertices_for_recording)
    def machine_vertices_for_recording(self, variable_to_record):
        return []

    @overrides(AbstractSplitterCommon.reset_called)
    def reset_called(self):
        pass
