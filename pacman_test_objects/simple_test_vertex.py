# Copyright (c) 2017-2023 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

""" test vertex used in many unit tests
"""
from pacman.model.partitioner_interfaces.legacy_partitioner_api import (
    LegacyPartitionerAPI)
from spinn_utilities.overrides import overrides
from pacman.model.graphs.application import ApplicationVertex
from pacman.model.graphs.machine import SimpleMachineVertex
from pacman.model.resources import ConstantSDRAM


class SimpleTestVertex(ApplicationVertex, LegacyPartitionerAPI):
    """
    test vertex
    """
    _model_based_max_atoms_per_core = None

    def __init__(self, n_atoms, label="testVertex", max_atoms_per_core=256,
                 fixed_sdram_value=None, splitter=None):
        super().__init__(
            label=label, max_atoms_per_core=max_atoms_per_core,
            splitter=splitter)
        self._model_based_max_atoms_per_core = max_atoms_per_core
        self._n_atoms = self.round_n_atoms(n_atoms, "test_param")
        self._fixed_sdram_value = fixed_sdram_value

    @overrides(LegacyPartitionerAPI.get_sdram_used_by_atoms)
    def get_sdram_used_by_atoms(self, vertex_slice):
        return ConstantSDRAM(
                self.get_sdram_usage_for_atoms(vertex_slice))

    def get_sdram_usage_for_atoms(self, vertex_slice):
        """
        :param vertex_slice: the atoms being considered
        :return: the amount of sdram (in bytes this model will use)
        """
        if self._fixed_sdram_value is None:
            return 1 * vertex_slice.n_atoms
        return self._fixed_sdram_value

    @overrides(LegacyPartitionerAPI.create_machine_vertex)
    def create_machine_vertex(self, vertex_slice, sdram, label=None):
        return SimpleMachineVertex(sdram, label, self, vertex_slice)

    @property
    @overrides(ApplicationVertex.n_atoms)
    def n_atoms(self):
        return self._n_atoms
