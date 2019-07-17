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
tests for placements
"""
import unittest
from pacman.model.graphs.machine import SimpleMachineVertex
from pacman.model.placements import Placement, Placements


class TestPlacements(unittest.TestCase):
    """
    tester for placements object in pacman.model.placements.placements
    """

    def test_create_new_placements(self):
        """
        test creating a placements object
        """
        subv = SimpleMachineVertex(None, "")
        pl = Placement(subv, 0, 0, 1)
        Placements([pl])

    def test_create_new_empty_placements(self):
        """
        checks that creating an empty placements object is valid
        """
        pls = Placements()
        self.assertEqual(pls._placements, dict())
        self.assertEqual(pls._machine_vertices, dict())

    def test_get_placement_of_vertex(self):
        """
        checks the placements get placement method
        """
        subv = list()
        for i in range(5):
            subv.append(SimpleMachineVertex(None, ""))

        pl = list()
        for i in range(4):
            pl.append(Placement(subv[i], 0, 0, i))

        pls = Placements(pl)
        for i in range(4):
            self.assertEqual(pls.get_placement_of_vertex(subv[i]), pl[i])

    def test_get_vertex_on_processor(self):
        """
        checks that from a placements object, you can get to the correct
        vertex using the get_vertex_on_processor() method
        """
        subv = list()
        for i in range(5):
            subv.append(SimpleMachineVertex(None, ""))

        pl = list()
        for i in range(4):
            pl.append(Placement(subv[i], 0, 0, i))

        pls = Placements(pl)
        for i in range(4):
            self.assertEqual(pls.get_vertex_on_processor(0, 0, i), subv[i])

        self.assertEqual(pls.get_placement_of_vertex(subv[0]), pl[0])

    def test_get_placements(self):
        """
        tests the placements iterator functionality.
        """
        subv = list()
        for i in range(5):
            subv.append(SimpleMachineVertex(None, ""))

        pl = list()
        for i in range(4):
            pl.append(Placement(subv[i], 0, 0, i))

        pls = Placements(pl)
        container = pls.placements
        for i in range(4):
            self.assertIn(pl[i], container)


if __name__ == '__main__':
    unittest.main()
