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
