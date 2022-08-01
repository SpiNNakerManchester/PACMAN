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

import sys
from spinn_utilities.overrides import overrides
from pacman.model.partitioner_interfaces import LegacyPartitionerAPI
from .application_vertex import ApplicationVertex
from pacman.model.resources import ConstantSDRAM
from pacman.model.graphs import (
    AbstractVirtual, AbstractSpiNNakerLink)
from pacman.model.graphs.machine import MachineSpiNNakerLinkVertex


class ApplicationSpiNNakerLinkVertex(
        ApplicationVertex, AbstractSpiNNakerLink, LegacyPartitionerAPI):
    """ A virtual vertex on a SpiNNaker Link.
    """

    __slots__ = [
        "_n_atoms",
        "_spinnaker_link_id",
        "_board_address"]

    def __init__(
            self, n_atoms, spinnaker_link_id, board_address=None, label=None,
            constraints=None, max_atoms_per_core=sys.maxsize):
        super().__init__(
            label=label, constraints=constraints,
            max_atoms_per_core=max_atoms_per_core)
        self._n_atoms = self.round_n_atoms(n_atoms)
        self._spinnaker_link_id = spinnaker_link_id
        self._board_address = board_address

    @property
    @overrides(AbstractSpiNNakerLink.spinnaker_link_id)
    def spinnaker_link_id(self):
        return self._spinnaker_link_id

    @property
    @overrides(AbstractVirtual.board_address)
    def board_address(self):
        return self._board_address

    @property
    @overrides(LegacyPartitionerAPI.n_atoms)
    def n_atoms(self):
        return self._n_atoms

    @overrides(LegacyPartitionerAPI.get_sdram_used_by_atoms)
    def get_sdram_used_by_atoms(self, vertex_slice):
        return ConstantSDRAM(0)

    @overrides(LegacyPartitionerAPI.create_machine_vertex)
    def create_machine_vertex(
            self, vertex_slice, sdram_required, label=None,
            constraints=None):
        machine_vertex = MachineSpiNNakerLinkVertex(
            self._spinnaker_link_id, self._board_address, label, constraints,
            self, vertex_slice)
        if sdram_required:
            assert (sdram_required == machine_vertex.sdram_required)
        return machine_vertex
