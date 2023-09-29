# Copyright (c) 2017 The University of Manchester
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

from pacman.model.graphs.common import Slice
from pacman.model.graphs.machine import SimpleMachineVertex
from pacman.model.resources import ConstantSDRAM


def get_resourced_machine_vertex(lo_atom, hi_atom, label=None):
    sdram_requirement = 4000 + 50 * (hi_atom - lo_atom)
    sdram = ConstantSDRAM(sdram_requirement)
    return SimpleMachineVertex(
        sdram, label=label, vertex_slice=Slice(lo_atom, hi_atom))
