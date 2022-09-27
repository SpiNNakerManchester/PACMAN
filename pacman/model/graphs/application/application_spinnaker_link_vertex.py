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

from spinn_utilities.overrides import overrides
from pacman.model.graphs.common.slice import Slice
from .application_virtual_vertex import ApplicationVirtualVertex


class ApplicationSpiNNakerLinkVertex(ApplicationVirtualVertex):
    """ A virtual application vertex on a SpiNNaker Link.
    """

    __slots__ = [
        "_n_atoms",
        "_spinnaker_link_id",
        "_board_address",
        "_n_machine_vertices",
        "_incoming",
        "_outgoing"]

    def __init__(
            self, n_atoms, spinnaker_link_id, board_address=None, label=None,
            n_machine_vertices=1, incoming=True, outgoing=True):
        """
        :param int n_atoms: The number of atoms in the vertex
        :param int spinnaker_link_id:
            The index of the spinnaker link to which the device is connected
        :param str board_address:
            The optional IP address of the board to which the device is
            connected e.g. in a multi-board system
        :param str label: The optional name of the vertex.
        """
        super().__init__(label=label)
        self._n_atoms = self.round_n_atoms(n_atoms)
        self._spinnaker_link_id = spinnaker_link_id
        self._board_address = board_address
        self._n_machine_vertices = n_machine_vertices
        self._incoming = incoming
        self._outgoing = outgoing

    @property
    @overrides(ApplicationVirtualVertex.n_atoms)
    def n_atoms(self):
        return self._n_atoms

    @property
    def spinnaker_link_id(self):
        """ The SpiNNaker link to which this device is connected
        :rtype: int
        """
        return self._spinnaker_link_id

    @property
    def board_address(self):
        """ The board to which this device is connected, or None for the
            default board

        :rtype: str or None
        """
        return self._board_address

    @property
    def n_machine_vertices(self):
        """ The number of machine vertices to create

        :rtype: int
        """
        return self._n_machine_vertices

    def get_incoming_slice(self, index):
        """ Get the slice to be given to the connection

        :param int index:
            The index of the connection, for when n_machine_vertices > 1

        :rtype: ~pacman.model.graphs.common.Slice
        """
        atoms_per_slice = self.n_atoms // self._n_machine_vertices
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
    def incoming(self):
        return self._incoming

    @property
    def outgoing(self):
        return self._outgoing

    @overrides(ApplicationVirtualVertex.get_outgoing_link_data)
    def get_outgoing_link_data(self, machine):
        if not self._outgoing:
            raise NotImplementedError("This vertex doesn't have outgoing data")
        return machine.get_spinnaker_link_with_id(
            self._spinnaker_link_id, self._board_address)
