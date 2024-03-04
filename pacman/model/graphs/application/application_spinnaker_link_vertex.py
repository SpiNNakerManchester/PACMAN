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
from typing import Optional
from spinn_utilities.overrides import overrides
from spinn_machine import Machine
from spinn_machine.link_data_objects import SpinnakerLinkData
from pacman.model.graphs.common.slice import Slice
from .application_virtual_vertex import ApplicationVirtualVertex


class ApplicationSpiNNakerLinkVertex(ApplicationVirtualVertex):
    """
    A virtual application vertex on a SpiNNaker Link.
    """

    __slots__ = (
        "_n_atoms",
        "_spinnaker_link_id",
        "_board_address",
        "_n_machine_vertices",
        "_incoming",
        "_outgoing")

    def __init__(
            self, n_atoms: int, spinnaker_link_id: int,
            board_address: Optional[str] = None, label: Optional[str] = None,
            n_machine_vertices: int = 1,
            incoming: bool = True, outgoing: bool = True):
        """
        :param int n_atoms: The number of atoms in the vertex
        :param int spinnaker_link_id:
            The index of the spinnaker link to which the device is connected
        :param str board_address:
            The optional IP address of the board to which the device is
            connected e.g. in a multi-board system
        :param str label: The optional name of the vertex.
        :param bool incoming:
        :param bool outgoing:
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
    def n_atoms(self) -> int:
        return self._n_atoms

    @property
    def spinnaker_link_id(self) -> int:
        """
        The SpiNNaker link to which this device is connected.

        :rtype: int
        """
        return self._spinnaker_link_id

    @property
    def board_address(self) -> Optional[str]:
        """
        The board to which this device is connected, or `None` for the
        default board.

        :rtype: str or None
        """
        return self._board_address

    @property
    def n_machine_vertices(self) -> int:
        """
        The number of machine vertices to create.

        :rtype: int
        """
        return self._n_machine_vertices

    def get_incoming_slice(self, index: int) -> Slice:
        """
        Get the slice to be given to the connection.

        :param int index:
            The index of the connection, for when n_machine_vertices > 1

        :rtype: ~pacman.model.graphs.common.Slice
        """
        atoms_per_slice = int(math.ceil(
            self._n_atoms / self._n_machine_vertices))
        low_atom = atoms_per_slice * index
        hi_atom = (atoms_per_slice * (index + 1)) - 1
        hi_atom = min((hi_atom, self.n_atoms - 1))
        return Slice(low_atom, hi_atom)

    def get_outgoing_slice(self) -> Slice:
        """
        Get the slice to be given to the outgoing connection.

        :rtype: ~pacman.model.graphs.common.Slice
        """
        return Slice(0, self.n_atoms - 1)

    @property
    def incoming(self) -> bool:
        """
        Reports if this vertex supports incoming links

        :rtype: bool
        """
        return self._incoming

    @property
    def outgoing(self) -> bool:
        """
        Reports if this vertex supports incoming links

        :rtype: bool
        """
        return self._outgoing

    @overrides(ApplicationVirtualVertex.get_outgoing_link_data)
    def get_outgoing_link_data(self, machine: Machine) -> SpinnakerLinkData:
        if not self._outgoing:
            raise NotImplementedError("This vertex doesn't have outgoing data")
        link = machine.get_spinnaker_link_with_id(
            self._spinnaker_link_id, self._board_address)
        assert link is not None, f"no link data for {self} on {machine}"
        return link

    @overrides(ApplicationVirtualVertex.get_max_atoms_per_core)
    def get_max_atoms_per_core(self) -> int:
        return int(math.ceil(self._n_atoms / self._n_machine_vertices))
