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

""" test vertex used in many unit tests
"""
from pacman.model.partitioner_interfaces.legacy_partitioner_api import (
    LegacyPartitionerAPI)
from spinn_utilities.overrides import overrides
from pacman.model.graphs.application import ApplicationVertex
from pacman.model.graphs.machine import SimpleMachineVertex
from pacman.model.resources import (
    ConstantSDRAM, DTCMResource, ResourceContainer, CPUCyclesPerTickResource)


class SimpleTestVertex(ApplicationVertex, LegacyPartitionerAPI):
    """
    test vertex
    """
    _model_based_max_atoms_per_core = None

    def __init__(self, n_atoms, label="testVertex", max_atoms_per_core=256,
                 constraints=None, fixed_sdram_value=None, splitter=None):
        super().__init__(
            label=label, max_atoms_per_core=max_atoms_per_core,
            constraints=constraints, splitter=splitter)
        self._model_based_max_atoms_per_core = max_atoms_per_core
        self._n_atoms = self.round_n_atoms(n_atoms, "test_param")
        self._fixed_sdram_value = fixed_sdram_value

    @overrides(LegacyPartitionerAPI.get_resources_used_by_atoms)
    def get_resources_used_by_atoms(self, vertex_slice):
        """
        standard method call to get the sdram, cpu and dtcm usage of a
        collection of atoms

        :param vertex_slice: the collection of atoms
        """
        return ResourceContainer(
            sdram=ConstantSDRAM(
                self.get_sdram_usage_for_atoms(vertex_slice)),
            cpu_cycles=CPUCyclesPerTickResource(
                self.get_cpu_usage_for_atoms(vertex_slice)),
            dtcm=DTCMResource(
                self.get_dtcm_usage_for_atoms(vertex_slice)))

    def get_cpu_usage_for_atoms(self, vertex_slice):
        """

        :param vertex_slice: the atoms being considered
        :return: the amount of cpu (in cycles this model will use)
        """
        return 1 * vertex_slice.n_atoms

    def get_dtcm_usage_for_atoms(self, vertex_slice):
        """

        :param vertex_slice: the atoms being considered
        :return: the amount of dtcm (in bytes this model will use)
        """
        return 1 * vertex_slice.n_atoms

    def get_sdram_usage_for_atoms(self, vertex_slice):
        """
        :param vertex_slice: the atoms being considered
        :return: the amount of sdram (in bytes this model will use)
        """
        if self._fixed_sdram_value is None:
            return 1 * vertex_slice.n_atoms
        return self._fixed_sdram_value

    @overrides(LegacyPartitionerAPI.create_machine_vertex)
    def create_machine_vertex(
            self, vertex_slice, sdram_required, label=None,
            constraints=None):
        return SimpleMachineVertex(
            sdram_required, label, constraints, self, vertex_slice)

    @property
    @overrides(LegacyPartitionerAPI.n_atoms)
    def n_atoms(self):
        return self._n_atoms
