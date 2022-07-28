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
from pacman.model.partitioner_interfaces import LegacyPartitionerAPI
from spinn_utilities.overrides import overrides
from .application_vertex import ApplicationVertex
from pacman.model.graphs import AbstractFPGA, AbstractVirtual
from pacman.model.graphs.machine import MachineFPGAVertex
from pacman.model.resources import ResourceContainer


class ApplicationFPGAVertex(
        ApplicationVertex, AbstractFPGA, LegacyPartitionerAPI):
    """ A virtual vertex on an FPGA link.
    """

    __slots__ = [
        "_fpga_id",
        "_fpga_link_id",
        "_board_address",
        "_n_atoms"]

    def __init__(
            self, n_atoms, fpga_id, fpga_link_id, board_address=None,
            label=None, constraints=None, max_atoms_per_core=sys.maxsize):
        super().__init__(
            label=label, constraints=constraints,
            max_atoms_per_core=max_atoms_per_core)

        self._n_atoms = self.round_n_atoms(n_atoms)
        self._fpga_id = fpga_id
        self._fpga_link_id = fpga_link_id
        self._board_address = board_address

    @property
    @overrides(AbstractFPGA.fpga_id)
    def fpga_id(self):
        return self._fpga_id

    @property
    @overrides(AbstractFPGA.fpga_link_id)
    def fpga_link_id(self):
        return self._fpga_link_id

    @property
    @overrides(AbstractVirtual.board_address)
    def board_address(self):
        return self._board_address

    @property
    @overrides(LegacyPartitionerAPI.n_atoms)
    def n_atoms(self):
        return self._n_atoms

    @overrides(LegacyPartitionerAPI.get_resources_used_by_atoms)
    def get_resources_used_by_atoms(self, vertex_slice):
        return ResourceContainer()

    @overrides(LegacyPartitionerAPI.create_machine_vertex)
    def create_machine_vertex(
            self, vertex_slice, sdram_required, label=None,
            constraints=None):
        machine_vertex = MachineFPGAVertex(
            self._fpga_id, self._fpga_link_id, self._board_address,
            label, constraints, self, vertex_slice)
        if sdram_required:
            assert (sdram_required == machine_vertex.sdram_required)
        return machine_vertex
