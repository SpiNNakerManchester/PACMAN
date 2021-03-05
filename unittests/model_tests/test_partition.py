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
from pacman.model.graphs.machine import SimpleMachineVertex
from pacman.model.constraints.partitioner_constraints import (
    MaxVertexAtomsConstraint, SameAtomsAsVertexConstraint,
    FixedVertexAtomsConstraint)


class TestPartitionConstraints(unittest.TestCase):
    """ Tester for pacman.model.constraints.partitioner_constraints
    """

    def test_max_vertex_atoms_constraint(self):
        c1 = MaxVertexAtomsConstraint(5)
        self.assertEqual(c1.size, 5)
        self.assertEqual(c1, MaxVertexAtomsConstraint(5))
        self.assertEqual(str(c1), 'MaxVertexAtomsConstraint(size=5)')
        c2 = MaxVertexAtomsConstraint(7)
        self.assertNotEqual(c1, c2)
        self.assertNotEqual(c1, "1.2.3.4")
        d = {}
        d[c1] = 1
        d[c2] = 2
        self.assertEqual(len(d), 2)

    def test_fixed_vertex_atoms_constraint(self):
        c1 = FixedVertexAtomsConstraint(5)
        self.assertEqual(c1.size, 5)
        self.assertEqual(c1, FixedVertexAtomsConstraint(5))
        self.assertEqual(str(c1), 'FixedVertexAtomsConstraint(size=5)')
        c2 = FixedVertexAtomsConstraint(7)
        self.assertNotEqual(c1, c2)
        self.assertNotEqual(c1, "1.2.3.4")
        d = {}
        d[c1] = 1
        d[c2] = 2
        self.assertEqual(len(d), 2)

    def test_same_atoms_as_vertex_constraint(self):
        with self.assertRaises(NotImplementedError):
            v1 = SimpleMachineVertex(None, "v1")
            v2 = SimpleMachineVertex(None, "v2")
            c1 = SameAtomsAsVertexConstraint(v1)
            self.assertEqual(c1.vertex, v1)
            self.assertEqual(c1, SameAtomsAsVertexConstraint(v1))
            self.assertEqual(str(c1), 'SameAtomsAsVertexConstraint(vertex=v1)')
            c2 = SameAtomsAsVertexConstraint(v2)
            self.assertNotEqual(c1, c2)
            self.assertNotEqual(c1, "1.2.3.4")
            d = {}
            d[c1] = 1
            d[c2] = 2
            self.assertEqual(len(d), 2)
