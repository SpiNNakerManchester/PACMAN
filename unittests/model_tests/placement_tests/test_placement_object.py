# Copyright (c) 2015 The University of Manchester
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

"""
tests for placement
"""
import unittest
from pacman.config_setup import unittest_setup
from pacman.data.pacman_data_writer import PacmanDataWriter
from pacman.exceptions import PacmanAlreadyPlacedError
from pacman.model.graphs.machine import SimpleMachineVertex
from pacman.model.placements import Placement, Placements


class ExtendedVertex1(SimpleMachineVertex):
    pass


class ExtendedVertex2(SimpleMachineVertex):
    pass


class ExtendedVertex3(SimpleMachineVertex):
    pass


class TestPlacement(unittest.TestCase):
    """
    tester for placement object in pacman.model.placements.placement
    """

    def setUp(self):
        unittest_setup()

    def test_create_new_placement(self):
        """
        test that creating a new placement puts stuff in the right place
        """
        subv = SimpleMachineVertex(None, "")
        pl = Placement(subv, 1, 2, 3)
        self.assertEqual(pl.x, 1)
        self.assertEqual(pl.y, 2)
        self.assertEqual(pl.p, 3)
        self.assertEqual(subv, pl.vertex)
        self.assertEqual((1, 2), pl.xy)
        self.assertFalse(pl.__eq__("pl"))
        pl2 = Placement(subv, 1, 2, 3)
        self.assertEqual(pl, pl2)
        self.assertEqual(hash(pl), hash(pl2))
        self.assertFalse(pl != pl2)

    def test_create_new_placements_duplicate_vertex(self):
        """
        check that you cant put a vertex in multiple placements
        """
        subv = SimpleMachineVertex(None, "")
        pl = list()
        for i in range(4):
            pl.append(Placement(subv, 0, 0, i))
        with self.assertRaises(PacmanAlreadyPlacedError):
            Placements(pl)

    def test_iterate_by_type(self):
        v1a = ExtendedVertex1(None)
        p1a = Placement(v1a, 0, 1, 1)
        v1b = ExtendedVertex1(None)
        p1b = Placement(v1b, 0, 2, 1)
        v2 = ExtendedVertex2(None)
        p2 = Placement(v2, 0, 0, 2)
        v3 = ExtendedVertex3(None)
        p3 = Placement(v3, 0, 0, 3)
        placements = Placements([p1a, p1b, p2, p3])
        l1 = list(placements.iterate_placements_by_vertex_type(
            ExtendedVertex1))
        self.assertListEqual(l1, [p1a, p1b])
        l2 = list(placements.iterate_placements_by_vertex_type(
            (ExtendedVertex2, ExtendedVertex1)))
        self.assertListEqual(l2, [p1a, p1b, p2])
        l3 = list(placements.iterate_placements_by_xy_and_type(
            (0, 0), (ExtendedVertex3, ExtendedVertex2)))
        self.assertListEqual(l3, [p2, p3])
        writer = PacmanDataWriter.setup()
        writer.set_placements(placements)
        l1 = list(writer.iterate_placements_by_vertex_type(
            ExtendedVertex1))
        self.assertListEqual(l1, [p1a, p1b])
        l2 = list(writer.iterate_placements_by_vertex_type(
            (ExtendedVertex2, ExtendedVertex1)))
        self.assertListEqual(l2, [p1a, p1b, p2])
        l3 = list(writer.iterate_placements_by_xy_and_type(
            (0, 0), (ExtendedVertex3, ExtendedVertex2)))
        self.assertListEqual(l3, [p2, p3])


if __name__ == '__main__':
    unittest.main()
