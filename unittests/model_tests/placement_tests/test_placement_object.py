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
from pacman.exceptions import PacmanAlreadyPlacedError
from pacman.model.graphs.machine import SimpleMachineVertex
from pacman.model.placements import Placement, Placements


class TestPlacement(unittest.TestCase):
    """
    tester for placement object in pacman.model.placements.placement
    """

    def test_create_new_placement(self):
        """
        test that creating a new placement puts stuff in the right place
        """
        subv = SimpleMachineVertex(None, "")
        pl = Placement(subv, 0, 0, 1)
        self.assertEqual(pl.x, 0)
        self.assertEqual(pl.y, 0)
        self.assertEqual(pl.p, 1)
        self.assertEqual(subv, pl.vertex)

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
