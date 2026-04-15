# Copyright (c) 2016 The University of Manchester
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
from __future__ import annotations
from typing import Iterable, List, Optional, TYPE_CHECKING
from spinn_utilities.overrides import overrides
from pacman.model.graphs.common.slice import Slice
from .application_virtual_vertex import ApplicationVirtualVertex
if TYPE_CHECKING:
    from spinn_machine.link_data_objects import FPGALinkData
    from spinn_machine import Machine
    from .fpga_connection import FPGAConnection


class ApplicationFPGAVertex(ApplicationVirtualVertex):
    """
    A virtual application vertex connected to one or more FPGA links.
    """

    __slots__ = (
        "_n_atoms",
        "_incoming_fpga_connections",
        "_outgoing_fpga_connection",
        "_n_machine_vertices_per_link")

    def __init__(
            self, n_atoms: int,
            incoming_fpga_connections: Optional[List[FPGAConnection]] = None,
            outgoing_fpga_connection: Optional[FPGAConnection] = None,
            label: Optional[str] = None,
            n_machine_vertices_per_link: int = 1):
        """
        :param n_atoms: The number of atoms in the vertex
        :param incoming_fpga_connections:
            The connections from one or more FPGAs that that packets are
            expected to be received from for this device, or `None` if no
            incoming traffic is expected from the device
        :param outgoing_fpga_connection:
            The connection to an FPGA that packets to be sent to this device
            should be sent down, or `None` if no outgoing traffic is expected
            to be sent to the device.
        :param label: The optional name of the vertex.
        :param n_machine_vertices_per_link:
            The optional number of machine vertices to create for each FPGA
            link (1 by default)
        """
        super().__init__(label=label)
        self._n_atoms = n_atoms
        self._incoming_fpga_connections = incoming_fpga_connections
        self._outgoing_fpga_connection = outgoing_fpga_connection
        self._n_machine_vertices_per_link = n_machine_vertices_per_link

    @property
    @overrides(ApplicationVirtualVertex.n_atoms)
    def n_atoms(self) -> int:
        return self._n_atoms

    @property
    def n_machine_vertices_per_link(self) -> int:
        """
        The number of machine vertices to create for each link of the FPGA.
        """
        return self._n_machine_vertices_per_link

    def get_incoming_slice_for_link(
            self, link: FPGAConnection, index: int) -> Slice:
        """
        :param link:
            The FPGA connection to get the slice for
        :param index:
            The index of the connection on the FGPA link, for when
            n_machine_vertices_per_link > 1
        :returns: The slice to be given to the connection from the given link.
        """
        # link used in subclasses but not here
        _ = link
        atoms_per_slice = self.n_atoms // self._n_machine_vertices_per_link
        low_atom = atoms_per_slice * index
        hi_atom = (atoms_per_slice * (index + 1)) - 1
        hi_atom = min((hi_atom, self.n_atoms - 1))
        return Slice(low_atom, hi_atom)

    def get_outgoing_slice(self) -> Slice:
        """
        :returns: The slice to be given to the outgoing connection.
        """
        return Slice(0, self.n_atoms - 1)

    @property
    def incoming_fpga_connections(self) -> Iterable[FPGAConnection]:
        """
        The connections from one or more FPGAs that packets are expected
        to be received from for this device.
        """
        if self._incoming_fpga_connections:
            yield from self._incoming_fpga_connections

    @property
    def outgoing_fpga_connection(self) -> Optional[FPGAConnection]:
        """
        The connection to one FPGA via one link to which packets are sent
        to this device.
        """
        return self._outgoing_fpga_connection

    @overrides(ApplicationVirtualVertex.get_outgoing_link_data)
    def get_outgoing_link_data(self, machine: Machine) -> FPGALinkData:
        fpga = self._outgoing_fpga_connection
        if fpga is None:
            raise NotImplementedError("This vertex doesn't have outgoing data")
        return machine.get_fpga_link_with_id(
            fpga.fpga_id, fpga.fpga_link_id, fpga.board_address,
            fpga.chip_coords)
