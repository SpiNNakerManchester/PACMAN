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
from pacman.config_setup import unittest_setup
from pacman.exceptions import (
    PacmanAlreadyExistsException, PacmanInvalidParameterException)
from pacman.model.graphs.application import ApplicationEdgePartition
from pacman_test_objects import SimpleTestEdge, SimpleTestVertex


class TestApplicationEdgeModel(unittest.TestCase):
    """
    tests which test the application graph object
    """

    def setUp(self):
        unittest_setup()

    def test_create_new_edge(self):
        """
        test that you can create a edge between two vertices
        """
        vert1 = SimpleTestVertex(10, "Vertex 1", 256)
        vert2 = SimpleTestVertex(5, "Vertex 2", 256)
        edge1 = SimpleTestEdge(vert1, vert2, "First edge")
        self.assertEqual(edge1.pre_vertex, vert1)
        self.assertEqual(edge1.post_vertex, vert2)

    def test_create_new_edge_without_label(self):
        """
        test initisation of a edge without a label
        """
        vert1 = SimpleTestVertex(10, "Vertex 1", 256)
        vert2 = SimpleTestVertex(5, "Vertex 2", 256)
        edge1 = SimpleTestEdge(vert1, vert2)
        self.assertEqual(edge1.pre_vertex, vert1)
        self.assertEqual(edge1.post_vertex, vert2)
        self.assertEqual(edge1.label, None)

    def test_partition(self):
        vert1 = SimpleTestVertex(10, "Vertex 1", 256)
        partition = ApplicationEdgePartition("spikes", vert1)
        vert2 = SimpleTestVertex(5, "Vertex 2", 256)
        edge1 = SimpleTestEdge(vert1, vert2)
        partition.add_edge(edge1)
        with self.assertRaises(PacmanAlreadyExistsException):
            partition.add_edge(edge1)
        with self.assertRaises(PacmanInvalidParameterException):
            partition.add_edge("edge")
        edge2 = SimpleTestEdge(vert1, vert2)
        self.assertNotIn(edge2, partition)
        partition.add_edge(edge2)
        self.assertEqual(2, partition.n_edges)
        self.assertIn(edge2, partition)
        self.assertIn("ApplicationEdgePartition", str(partition))
        self.assertIn("spikes", repr(partition))
