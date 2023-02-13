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

"""
tests for placement
"""
import unittest
from pacman.config_setup import unittest_setup
from pacman.exceptions import PacmanAlreadyPlacedError
from pacman.model.graphs.machine import SimpleMachineVertex
from pacman.model.placements import Placement, Placements


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


if __name__ == '__main__':
    unittest.main()
