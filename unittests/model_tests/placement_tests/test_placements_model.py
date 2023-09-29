# Copyright (c) 2014 The University of Manchester
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
tests for placements
"""
import unittest
from pacman.config_setup import unittest_setup
from pacman.exceptions import (
    PacmanNotPlacedError, PacmanProcessorAlreadyOccupiedError,
    PacmanProcessorNotOccupiedError)
from pacman.model.graphs.machine import SimpleMachineVertex
from pacman.model.placements import Placement, Placements


class TestPlacements(unittest.TestCase):
    """
    tester for placements object in pacman.model.placements.placements
    """

    def setUp(self):
        unittest_setup()

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
            self.assertEqual(
                pls.get_placement_on_processor(0, 0, i).vertex, subv[i])

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

        pls = Placements(pl).placements
        for i in range(4):
            self.assertIn(pl[i], pls)

    def test_safety_code(self):
        subv = SimpleMachineVertex(None, "1")
        pl = Placement(subv, 0, 0, 1)
        pls = Placements([pl])
        subv2 = SimpleMachineVertex(None, "2")
        pl2 = Placement(subv2, 0, 0, 1)
        with self.assertRaises(PacmanProcessorAlreadyOccupiedError):
            pls.add_placement(pl2)
        with self.assertRaises(PacmanProcessorNotOccupiedError):
            pls.get_placement_on_processor(0, 0, 2)
        with self.assertRaises(PacmanProcessorNotOccupiedError):
            pls.get_placement_on_processor(1, 1, 2)
        with self.assertRaises(PacmanNotPlacedError):
            pls.get_placement_of_vertex(subv2)

    def test_infos_code(self):
        subv = SimpleMachineVertex(None, "1")
        pl = Placement(subv, 0, 0, 1)
        pls = Placements([pl])
        subv2 = SimpleMachineVertex(None, "2")
        pl2 = Placement(subv2, 0, 0, 2)
        pls.add_placement(pl2)

        self.assertTrue(pls.is_processor_occupied(0, 0, 1))
        self.assertFalse(pls.is_processor_occupied(0, 0, 3))
        self.assertFalse(pls.is_processor_occupied(0, 1, 1))
        self.assertEqual(2, pls.n_placements_on_chip(0, 0))
        self.assertEqual(0, pls.n_placements_on_chip(0, 2))
        self.assertListEqual([(0, 0)], list(pls.chips_with_placements))
        self.assertEqual("(0, 0)", repr(pls))
        self.assertEqual(2, len(pls))


if __name__ == '__main__':
    unittest.main()
