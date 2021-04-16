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

from pacman.model.graphs.common import Slice
from pacman.model.graphs.machine import SimpleMachineVertex
from pacman.model.resources import (
    ConstantSDRAM, CPUCyclesPerTickResource, DTCMResource, ResourceContainer)


def get_resourced_machine_vertext(lo_atom, hi_atom, label=None):
    cpu_cycles = 10 * (hi_atom - lo_atom)
    dtcm_requirement = 200 * (hi_atom - lo_atom)
    sdram_requirement = 4000 + 50 * (hi_atom - lo_atom)
    resources = ResourceContainer(
        cpu_cycles=CPUCyclesPerTickResource(cpu_cycles),
        dtcm=DTCMResource(dtcm_requirement),
        sdram=ConstantSDRAM(sdram_requirement))
    return SimpleMachineVertex(
        resources, label=label, vertex_slice=Slice(lo_atom, hi_atom))