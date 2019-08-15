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
from pacman.model.resources import (
    ConstantSDRAM, CPUCyclesPerTickResource, DTCMResource, IPtagResource,
    ResourceContainer, VariableSDRAM)
from pacman.model.routing_info import BaseKeyAndMask
from pacman.utilities.json_utils import (
    constraint_to_json, constraint_from_json,
    resource_container_to_json, resource_container_from_json,
    vertex_to_json, vertex_from_json)
from pacman.model.graphs.machine import SimpleMachineVertex


class TestJsonUtils(unittest.TestCase):

    def compare_constraint(self, c1, c2):
        if c1 == c2:
            return
        if c1.__class__ != c2.__class__:
            raise AssertionError("{} != {}".format(
                c1.__class__, c2.__class__))
        self.assertEqual(c1.vertex.label, c2.vertex.label)

    def constraint_there_and_back(self, there):
        j_object = constraint_to_json(there)
        back = constraint_from_json(j_object)
        self.compare_constraint(there, back)

    def resource_there_and_back(self, there):
        j_object = resource_container_to_json(there)
        back = resource_container_from_json(j_object)
        self.assertEqual(there, back)

    def vertext_there_and_back(self, there):
        j_object = vertex_to_json(there)
        back = vertex_from_json(j_object)
        self.assertEqual(there.label, back.label)
        self.assertEqual(there.resources_required, back.resources_required)
        self.assertCountEqual(there.constraints, back.constraints)
        for c1, c2 in zip(there.constraints, back.constraints) :
            self.compare_constraint(c1, c2)

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
        self.constraint_there_and_back(c1)

    def test_same_atoms_as_vertex_constraint(self):
        v1 = SimpleMachineVertex(None, "v1")
        c1 = SameAtomsAsVertexConstraint(v1)
        self.constraint_there_and_back(c1)

    def test_max_vertex_atoms_constraint(self):
        c1 = MaxVertexAtomsConstraint(5)
        self.constraint_there_and_back(c1)

    def test_fixed_vertex_atoms_constraint(self):
        c1 = FixedVertexAtomsConstraint(5)
        self.constraint_there_and_back(c1)

    def test_contiguous_key_range_constraint(self):
        c1 = ContiguousKeyRangeContraint()
        self.constraint_there_and_back(c1)

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

    def test_vertex(self):
        s1 = SimpleMachineVertex(ResourceContainer(iptags=[IPtagResource(
            "127.0.0.1", port=None, strip_sdp=True)]),
            label="Vertex")
        self.vertext_there_and_back(s1)

    def test_vertex2(self):
        c1 = ContiguousKeyRangeContraint()
        c2 = BoardConstraint("1.2.3.4")
        s1 = SimpleMachineVertex(ResourceContainer(iptags=[IPtagResource(
            "127.0.0.1", port=None, strip_sdp=True)]),
            label="Vertex", constraints=[c1, c2])
        self.vertext_there_and_back(s1)

    def test_same_chip_as_constraint_plus(self):
        v1 = SimpleMachineVertex(None, "v1")
        c1 = SameChipAsConstraint(v1)
        self.constraint_there_and_back(c1)
