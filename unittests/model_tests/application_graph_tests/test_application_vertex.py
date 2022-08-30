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
from pacman.exceptions import (
    PacmanConfigurationException, PacmanInvalidParameterException)
from pacman.model.routing_info import BaseKeyAndMask
from pacman.model.constraints.key_allocator_constraints import (
    FixedKeyAndMaskConstraint)
from pacman.model.graphs.common import Slice
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

    def test_create_new_vertex_with_constraint_list(self):
        """
        test initialisation of a vertex with a max size constraint
        """
        constraint = FixedKeyAndMaskConstraint([
            BaseKeyAndMask(0xFF0, 0xFF8)])
        vert = SimpleTestVertex(10, "New AbstractConstrainedVertex", 256)
        vert.add_constraint(constraint)
        self.assertEqual(vert.n_atoms, 10)
        self.assertEqual(vert.label, "New AbstractConstrainedVertex")
        self.assertIsNotNone(repr(vert))
        assert constraint in vert.constraints
        with self.assertRaises(PacmanInvalidParameterException):
            vert.add_constraint(None)
        with self.assertRaises(PacmanInvalidParameterException):
            vert.add_constraint("Bacon")

    def test_create_new_vertex_add_constraints(self):
        """
        test that creating a vertex and then adding constraints in a list
        """
        constraint1 = FixedKeyAndMaskConstraint([
            BaseKeyAndMask(0xFF0, 0xFF8)])
        # Ignore that these two dont make sense together
        constraint2 = FixedKeyAndMaskConstraint([
            BaseKeyAndMask(0xFF0, 0xFF7)])
        constr = list()
        constr.append(constraint1)
        constr.append(constraint2)
        vert = SimpleTestVertex(10, "New AbstractConstrainedVertex", 256)
        vert.add_constraints(constr)
        self.assertEqual(vert.n_atoms, 10)
        self.assertEqual(vert.label, "New AbstractConstrainedVertex")
        self.assertEqual(len(vert.constraints), 2)
        for constraint in constr:
            self.assertIn(constraint, vert.constraints)

    def test_create_vertex_from_vertex_with_previous_constraints(self):
        """
        test the create vertex command given by the
        vertex actually works and generates a vertex
        with the same constraints mapped over
        """
        constraint1 = FixedKeyAndMaskConstraint([
            BaseKeyAndMask(0xFF0, 0xFF8)])
        vert = SimpleTestVertex(10, "New AbstractConstrainedVertex", 256)
        subv_from_vert = vert.create_machine_vertex(
            Slice(0, 9),
            vert.get_sdram_used_by_atoms(Slice(0, 9)))
        self.assertNotIn(constraint1, subv_from_vert.constraints)

    def test_new_create_vertex_from_vertex_no_constraints(self):
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

    def test_create_new_vertex_from_vertex_with_additional_constraints(
            self):
        """
        test that a vertex created from a vertex with
        constraints can have more constraints added to it.
        """
        constraint1 = FixedKeyAndMaskConstraint([
            BaseKeyAndMask(0xFF0, 0xFF8)])
        # Ignore that these two dont make sense together
        constraint2 = FixedKeyAndMaskConstraint([
            BaseKeyAndMask(0xFF0, 0xFF7)])
        vert = SimpleTestVertex(10, "New AbstractConstrainedVertex", 256)
        vert.add_constraint(constraint1)
        subv_from_vert = vert.create_machine_vertex(
            Slice(0, 9),
            vert.get_sdram_used_by_atoms(Slice(0, 9)), "",
            [constraint2])
        subv_from_vert.add_constraint(constraint1)
        self.assertEqual(len(subv_from_vert.constraints), 2)
        self.assertIn(constraint1, subv_from_vert.constraints)
        self.assertIn(constraint2, subv_from_vert.constraints)

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

    def test_max_atoms(self):
        vert = SimpleTestVertex(5)
        self.assertEqual(256, vert.get_max_atoms_per_core())
        vert.set_max_atoms_per_core(100)
        self.assertEqual(100, vert.get_max_atoms_per_core())
