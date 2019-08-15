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
import unittest

from pacman.model.constraints.key_allocator_constraints import (
    ContiguousKeyRangeContraint, FixedKeyAndMaskConstraint,
    FixedMaskConstraint, ShareKeyConstraint)
from pacman.model.constraints.placer_constraints import (
    BoardConstraint, ChipAndCoreConstraint, RadialPlacementFromChipConstraint,
    SameChipAsConstraint)
from pacman.model.constraints.partitioner_constraints import (
    MaxVertexAtomsConstraint, SameAtomsAsVertexConstraint,
    FixedVertexAtomsConstraint)
from pacman.model.resources import ResourceContainer, IPtagResource
from pacman.model.routing_info import BaseKeyAndMask
from pacman.model.resources import (
    ConstantSDRAM, CPUCyclesPerTickResource, DTCMResource, IPtagResource,
    ResourceContainer, VariableSDRAM)
from pacman.utilities.json_utils import constraint_to_json, contraint_from_json, resource_container_to_json, resource_container_from_json
from pacman.model.graphs.machine import SimpleMachineVertex


class TestJsonUtils(unittest.TestCase):

    def constraint_there_and_back(self, there):
        j_object = constraint_to_json(there)
        back = contraint_from_json(j_object)
        self.assertEqual(there, back)

    def resource_there_and_back(self, there):
        j_object = resource_container_to_json(there)
        back = resource_container_from_json(j_object)
        self.assertEqual(there, back)

    def there_and_back_by_vertex(self, there):
        j_object = constraint_to_json(there)
        back = contraint_from_json(j_object)
        self.assertEqual(there.vertex.label, back.vertex.label)

    def test_board_constraint(self):
        c1 = BoardConstraint("1.2.3.4")
        self.constraint_there_and_back(c1)

    def test_chip_and_core_constraint(self):
        c1 = ChipAndCoreConstraint(1, 2)
        self.constraint_there_and_back(c1)
        c2 = ChipAndCoreConstraint(1, 2, 3)
        self.constraint_there_and_back(c2)

    def test_radial_placement_from_chip_constraint(self):
        c1 = RadialPlacementFromChipConstraint(1, 2)
        self.constraint_there_and_back(c1)

    def test_same_chip_as_constraint(self):
        v1 = SimpleMachineVertex(None, "v1")
        c1 = SameChipAsConstraint(v1)
        self.there_and_back_by_vertex(c1)

    def test_same_atoms_as_vertex_constraint(self):
        v1 = SimpleMachineVertex(None, "v1")
        c1 = SameAtomsAsVertexConstraint(v1)
        self.there_and_back_by_vertex(c1)

    def test_max_vertex_atoms_constraint(self):
        c1 = MaxVertexAtomsConstraint(5)
        self.constraint_there_and_back(c1)

    def test_fixed_vertex_atoms_constraint(self):
        c1 = FixedVertexAtomsConstraint(5)
        self.constraint_there_and_back(c1)

    def test_contiguous_key_range_constraint(self):
        c1 = ContiguousKeyRangeContraint()

    def test_fixed_key_and_mask_constraint(self):
        c1 = FixedKeyAndMaskConstraint([
            BaseKeyAndMask(0xFF0, 0xFF8)])
        self.constraint_there_and_back(c1)
        km = BaseKeyAndMask(0xFF0, 0xFF8)
        km2 = BaseKeyAndMask(0xFE0, 0xFF8)
        c2 = FixedKeyAndMaskConstraint([km, km2])
        self.constraint_there_and_back(c2)

    def test_fixed_mask_constraint(self):
        c1 = FixedMaskConstraint(0xFF0)
        self.constraint_there_and_back(c1)

    def test_tags_resources(self):
        t1 = IPtagResource("1", 2, True)  # Minimal args
        r1 = ResourceContainer(iptags=[t1])
        self.resource_there_and_back(r1)
        t2 = IPtagResource("1.2.3.4", 2, False, 4, 5)
        r2 = ResourceContainer(reverse_iptags=[t2])
        self.resource_there_and_back(r2)

    def test_resource_coontainer(self):
        sdram1 = ConstantSDRAM(128 * (2**20))
        dtcm = DTCMResource(128 * (2**20) + 1)
        cpu = CPUCyclesPerTickResource(128 * (2**20) + 2)
        r1 = ResourceContainer(dtcm, sdram1, cpu)
        self.resource_there_and_back(r1)
        sdram2 = VariableSDRAM(10, 20)
        t1 = IPtagResource("1", 2, True)  # Minimal args
        t2 = IPtagResource("1.2.3.4", 2, False, 4, 5)
        r2 = r1 = ResourceContainer(dtcm, sdram1, cpu, iptags=[t1, t2])
        self.resource_there_and_back(r2)
