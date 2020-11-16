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
from pacman.model.constraints.placer_constraints import (
    ChipAndCoreConstraint)
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
        "_virtual_chip_x",
        "_virtual_chip_y",
        "_n_atoms"]

    def __init__(
            self, n_atoms, fpga_id, fpga_link_id, board_address=None,
            label=None, constraints=None, max_atoms_per_core=sys.maxsize):
        super(ApplicationFPGAVertex, self).__init__(
            label=label, constraints=constraints,
            max_atoms_per_core=max_atoms_per_core)

        self._n_atoms = n_atoms
        self._fpga_id = fpga_id
        self._fpga_link_id = fpga_link_id
        self._board_address = board_address
        self._virtual_chip_x = None
        self._virtual_chip_y = None

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
    @overrides(AbstractVirtual.virtual_chip_x)
    def virtual_chip_x(self):
        return self._virtual_chip_x

    @property
    @overrides(AbstractVirtual.virtual_chip_y)
    def virtual_chip_y(self):
        return self._virtual_chip_y

    @overrides(AbstractVirtual.set_virtual_chip_coordinates)
    def set_virtual_chip_coordinates(self, virtual_chip_x, virtual_chip_y):
        if virtual_chip_x is not None and virtual_chip_y is not None:
            self._virtual_chip_x = virtual_chip_x
            self._virtual_chip_y = virtual_chip_y
            if len(self._machine_vertices) != 0:
                for machine_vertex in self._machine_vertices:
                    if (machine_vertex.virtual_chip_x != self._virtual_chip_x
                            or machine_vertex.virtual_chip_y !=
                            virtual_chip_y):
                        machine_vertex.set_virtual_chip_coordinates(
                            self._virtual_chip_x, self._virtual_chip_y)
            else:
                self.add_constraint(ChipAndCoreConstraint(
                    self._virtual_chip_x, self._virtual_chip_y))

    @property
    @overrides(LegacyPartitionerAPI.n_atoms)
    def n_atoms(self):
        return self._n_atoms

    @overrides(LegacyPartitionerAPI.get_resources_used_by_atoms)
    def get_resources_used_by_atoms(self, vertex_slice):
        return ResourceContainer()

    @overrides(LegacyPartitionerAPI.create_machine_vertex)
    def create_machine_vertex(
            self, vertex_slice, resources_required, label=None,
            constraints=None):
        machine_vertex = MachineFPGAVertex(
            self._fpga_id, self._fpga_link_id, self._board_address,
            label, constraints, self, vertex_slice)
        machine_vertex.set_virtual_chip_coordinates(
            self._virtual_chip_x, self._virtual_chip_y)
        if resources_required:
            assert (resources_required == machine_vertex.resources_required)
        return machine_vertex
