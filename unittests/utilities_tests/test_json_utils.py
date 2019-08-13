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

from pacman.model.constraints.placer_constraints import (
    BoardConstraint, ChipAndCoreConstraint, RadialPlacementFromChipConstraint,
    SameChipAsConstraint)
from pacman.model.constraints.partitioner_constraints import (
    MaxVertexAtomsConstraint, SameAtomsAsVertexConstraint,
    FixedVertexAtomsConstraint)
from pacman.utilities.json_utils import constraint_to_json, contraint_from_json
from pacman.model.graphs.machine import SimpleMachineVertex


class TestJsonUtils(unittest.TestCase):

    def there_and_back(self, there):
        j_object = constraint_to_json(there)
        back = contraint_from_json(j_object)
        self.assertEqual(there, back)

    def there_and_back_by_vertex(self, there):
        j_object = constraint_to_json(there)
        back = contraint_from_json(j_object)
        self.assertEqual(there.vertex.label, back.vertex.label)

    def test_board_constraint(self):
        c1 = BoardConstraint("1.2.3.4")
        self.there_and_back(c1)

    def test_chip_and_core_constraint(self):
        c1 = ChipAndCoreConstraint(1, 2)
        self.there_and_back(c1)
        c2 = ChipAndCoreConstraint(1, 2, 3)
        self.there_and_back(c2)

    def test_radial_placement_from_chip_constraint(self):
        c1 = RadialPlacementFromChipConstraint(1, 2)
        self.there_and_back(c1)

    def test_same_chip_as_constraint(self):
        v1 = SimpleMachineVertex(None, "v1")
        c1 = SameChipAsConstraint(v1)
        self.there_and_back_by_vertex(c1)

    def test_same_atoms_as_vertex_constraint(self):
        v1 = SimpleMachineVertex(None, "v1")
        c1 = SameAtomsAsVertexConstraint(v1)
        self.there_and_back_by_vertex(c1)
