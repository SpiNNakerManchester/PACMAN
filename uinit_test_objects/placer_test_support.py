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

from pacman.model.graphs.application import ApplicationVertex
from pacman.model.graphs.common import Slice
from pacman.model.graphs.machine import SimpleMachineVertex
from pacman.model.resources import (
    ConstantSDRAM, CPUCyclesPerTickResource, DTCMResource, ResourceContainer)


def get_resources_used_by_atoms(lo_atom, hi_atom, vertex_in_edges):
    vertex = Vertex(1, None)
    cpu_cycles = vertex.get_cpu_usage_for_atoms(lo_atom, hi_atom)
    dtcm_requirement = vertex.get_dtcm_usage_for_atoms(lo_atom, hi_atom)
    sdram_requirement = vertex.get_sdram_usage_for_atoms(
        Slice(lo_atom, hi_atom))
    return ResourceContainer(
        cpu_cycles=CPUCyclesPerTickResource(cpu_cycles),
        dtcm=DTCMResource(dtcm_requirement),
        sdram=ConstantSDRAM(sdram_requirement))


class Vertex(ApplicationVertex):
    def __init__(self, n_atoms, label):
        super(Vertex, self).__init__(label=label, max_atoms_per_core=256)
        self._n_atoms = n_atoms
        self._model_based_max_atoms_per_core = 256

    @property
    def n_atoms(self):
        return self._n_atoms

    def get_cpu_usage_for_atoms(self, lo_atom, hi_atom):
        return 10 * (hi_atom - lo_atom)

    def get_dtcm_usage_for_atoms(self, lo_atom, hi_atom):
        return 200 * (hi_atom - lo_atom)

    def get_sdram_usage_for_atoms(self, vertex_slice):
        return 4000 + 50 * (vertex_slice.hi_atom - vertex_slice.lo_atom)

    def create_machine_vertex(
            self, vertex_slice, resources_required, label=None,
            constraints=None):
        pass

    def get_resources_used_by_atoms(self, vertex_slice):
        pass


class MachineVertex(SimpleMachineVertex):
    def __init__(self, lo_atom, hi_atom, resources_required, label=None,
                 constraints=None):
        super(MachineVertex, self).__init__(
            resources_required, label=label, constraints=constraints)
        self.lo_atom = lo_atom
        self.hi_atom = hi_atom
        self._model_based_max_atoms_per_core = 256
        self.n_atoms = hi_atom - lo_atom
