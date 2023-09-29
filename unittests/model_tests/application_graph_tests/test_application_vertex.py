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

import numpy
import unittest
from pacman.config_setup import unittest_setup
from pacman.exceptions import (
    PacmanConfigurationException, PacmanInvalidParameterException)
from pacman.model.graphs.common import Slice, ChipAndCore
from pacman.model.graphs.machine import SimpleMachineVertex
from pacman.model.partitioner_splitters import SplitterFixedLegacy
from pacman_test_objects import SimpleTestVertex


class MockSplitter(SplitterFixedLegacy):

    reset_seen = False

    def reset_called(self):
        self.reset_seen = True


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
        self.assertIsNone(vert.get_fixed_location())
        vert.set_fixed_location(0, 0, 1)
        self.assertEqual(vert.get_fixed_location(), ChipAndCore(0, 0, 1))
        with self.assertRaises(PacmanConfigurationException):
            vert.set_fixed_location(0, 0)
        vert.set_fixed_location(0, 0, 1)

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
        """
        check that the creation of a vertex means that the resources
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

    def test_set_splitter(self):
        split1 = MockSplitter()
        vert = SimpleTestVertex(5, splitter=split1)
        self.assertEqual(split1, vert.splitter)
        vert.splitter = split1
        self.assertEqual(split1, vert.splitter)
        split2 = MockSplitter()
        with self.assertRaises(PacmanConfigurationException):
            vert.splitter = split2
        self.assertFalse(split1.reset_seen)
        vert.reset()
        self.assertTrue(split1.reset_seen)

    def test_set_label(self):
        vert = SimpleTestVertex(5)
        vert.set_label("test 1")
        self.assertEqual("test 1", vert.label)
        vert.addedToGraph()
        with self.assertRaises(PacmanConfigurationException):
            vert.set_label("test 2")
