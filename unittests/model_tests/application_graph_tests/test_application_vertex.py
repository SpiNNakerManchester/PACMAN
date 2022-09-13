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

import numpy
import unittest
from pacman.config_setup import unittest_setup
from pacman.exceptions import PacmanInvalidParameterException

from pacman.model.graphs.common import Slice, ChipAndCore
from pacman.model.graphs.machine import SimpleMachineVertex
from pacman_test_objects import SimpleTestVertex
from pacman.exceptions import (
    PacmanConfigurationException, PacmanInvalidParameterException)


class TestApplicationGraphModel(unittest.TestCase):
    """
    tests which test the application graph object
    """

    def setUp(self):
        unittest_setup()

    def test_create_new_vertex(self):
        """
        test initialisation of a vertex
        """
        vert = SimpleTestVertex(10, "New AbstractConstrainedVertex", 256)
        self.assertEqual(vert.n_atoms, 10)
        self.assertEqual(vert.label, "New AbstractConstrainedVertex")

    def test_create_new_vertex_without_label(self):
        """
        test initialisation of a vertex without a label
        """
        vert = SimpleTestVertex(10, "Population", 256)
        self.assertEqual(vert.n_atoms, 10)
        pieces = vert.label.split(" ")
        self.assertIn(pieces[0], "Population n")

    def test_create_new_vertex_add_fixed(self):
        """
        test that creating a vertex and then adding fixed_locations
        """
        vert = SimpleTestVertex(10, "New AbstractConstrainedVertex", 256)
        self.assertIsNone(vert.fixed_location)
        vert.fixed_location = ChipAndCore(0, 0, 1)
        self.assertEqual(vert.fixed_location, ChipAndCore(0, 0, 1))
        with self.assertRaises(PacmanConfigurationException):
            vert.fixed_location = ChipAndCore(0, 1, 2)
        with self.assertRaises(PacmanInvalidParameterException):
            vert.fixed_location = None
        vert.fixed_location = ChipAndCore(0, 0, 1)

    def test_new_create_vertex_from_vertex_no_fixed(self):
        """
        test the creating of a vertex by the
        create vertex method will actually create a vertex of the
        vertex type.
        """
        vert = SimpleTestVertex(10, "New AbstractConstrainedVertex", 256)
        vertex = vert.create_machine_vertex(
            Slice(0, 9),
            vert.get_sdram_used_by_atoms(Slice(0, 9)))
        self.assertIsInstance(vertex, SimpleMachineVertex)

    def test_new_create_vertex_from_vertex_check_resources(self):
        """ check that the creation of a vertex means that the resources
        calculated by the vertex is the same as what the
        vertex says (given same sizes)

        """
        vert = SimpleTestVertex(10, "New AbstractConstrainedVertex", 256)
        sdram = vert.get_sdram_used_by_atoms(Slice(0, 9))
        subv_from_vert = vert.create_machine_vertex(Slice(0, 9), sdram, "")
        self.assertEqual(subv_from_vert.sdram_required, sdram)

    def test_round_n_atoms(self):
        # .1 is not exact in floating point
        near = .1 + .1 + .1 + .1 + .1 + .1 + .1 + .1 + .1 + .1
        self.assertNotEqual(1, near)
        vert = SimpleTestVertex(near)
        self.assertEqual(1, vert.n_atoms)
        with self.assertRaises(PacmanInvalidParameterException):
            SimpleTestVertex(1.5)
        vert = SimpleTestVertex(numpy.int64(23))
        self.assertTrue(isinstance(vert.n_atoms, int))
