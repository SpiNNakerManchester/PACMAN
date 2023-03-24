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

import math
from pacman.exceptions import PacmanInvalidParameterException
from spinn_utilities.overrides import overrides
from pacman.model.graphs.common.slice import Slice
from .application_virtual_vertex import ApplicationVirtualVertex


class ApplicationFPGAVertex(ApplicationVirtualVertex):
    """ A virtual application vertex connected to one or more FPGA links
    """

    __slots__ = [
        "_n_atoms",
        "_incoming_fpga_connections",
        "_outgoing_fpga_connection",
        "_n_machine_vertices_per_link"]

    def __init__(
            self, n_atoms, incoming_fpga_connections=None,
            outgoing_fpga_connection=None, label=None,
            n_machine_vertices_per_link=1):
        """

        :param int n_atoms: The number of atoms in the vertex
        :param incoming_fpga_connections:
            The connections from one or more FPGAs that that packets are
            expected to be received from for this device, or None if no
            incoming traffic is expected from the device
        :type incoming_fpga_connections: list(FPGAConnection) or None
        :param outgoing_fpga_connection:
            The connection to an FPGA that packets to be sent to this device
            should be sent down, or None if no outgoing traffic is expected to
            be sent to the device.
        :type outgoing_fpga_connection: FPGAConnection or None
        :param str label: The optional name of the vertex.
        :param int n_machine_vertices_per_link:
            The optional number of machine vertices to create for each FPGA
            link (1 by default)
        """
        super().__init__(label=label)
        self._n_atoms = n_atoms
        self._incoming_fpga_connections = incoming_fpga_connections
        self._outgoing_fpga_connection = outgoing_fpga_connection
        self._n_machine_vertices_per_link = n_machine_vertices_per_link

        if (outgoing_fpga_connection is not None and
                not outgoing_fpga_connection.is_concrete):
            raise PacmanInvalidParameterException(
                "outgoing_fpga_connection", outgoing_fpga_connection,
                "The outgoing connection must have a specific FPGA ID and "
                "link ID")

    @property
    @overrides(ApplicationVirtualVertex.n_atoms)
    def n_atoms(self):
        return self._n_atoms

    @property
    def n_machine_vertices_per_link(self):
        """ The number of machine vertices to create for each link of the FPGA
        :rtype: int
        """
        return self._n_machine_vertices_per_link

    def get_incoming_slice_for_link(self, link, index):
        """ Get the slice to be given to the connection from the given link

        :param FPGAConnection link: The FPGA connection to get the slice for
        :param int index:
            The index of the connection on the FGPA link, for when
            n_machine_vertices_per_link > 1

        :rtype: ~pacman.model.graphs.common.Slice
        """
        # pylint: disable=unused-argument
        atoms_per_slice = int(math.ceil(
            self.n_atoms / self._n_machine_vertices_per_link))
        low_atom = atoms_per_slice * index
        hi_atom = (atoms_per_slice * (index + 1)) - 1
        hi_atom = min((hi_atom, self.n_atoms - 1))
        return Slice(low_atom, hi_atom)

    def get_outgoing_slice(self):
        """ Get the slice to be given to the outgoing connection

        :rtype: ~pacman.model.graphs.common.Slice
        """
        return Slice(0, self.n_atoms - 1)

    @property
    def incoming_fpga_connections(self):
        """ The connections from one or more FPGAs that packets are expected
            to be received from for this device

        :rtype: iter(FPGAConnection)
        """
        if self._incoming_fpga_connections:
            for conn in self._incoming_fpga_connections:
                yield from conn.expanded

    @property
    def outgoing_fpga_connection(self):
        """ The connection to one FPGA via one link to which packets are sent
            to this device.

        :rtype: FPGAConnection or None
        """
        return self._outgoing_fpga_connection

    @overrides(ApplicationVirtualVertex.get_outgoing_link_data)
    def get_outgoing_link_data(self, machine):
        if self._outgoing_fpga_connection is None:
            raise NotImplementedError("This vertex doesn't have outgoing data")
        fpga = self._outgoing_fpga_connection
        return machine.get_fpga_link_with_id(
            fpga.fpga_id, fpga.fpga_link_id, fpga.board_address,
            fpga.chip_coords)

    @overrides(ApplicationVirtualVertex.get_max_atoms_per_core)
    def get_max_atoms_per_core(self):
        return int(math.ceil(
            self._n_atoms / self._n_machine_vertices_per_link))
