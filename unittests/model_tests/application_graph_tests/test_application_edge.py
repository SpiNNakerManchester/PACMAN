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

import unittest
from pacman.config_setup import unittest_setup
from pacman.exceptions import (
    PacmanAlreadyExistsException, PacmanConfigurationException,
    PacmanInvalidParameterException)
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
        vert3 = SimpleTestVertex(5, "Vertex 3", 256)
        edge3 = SimpleTestEdge(vert3, vert2)
        with self.assertRaises(PacmanConfigurationException):
            partition.add_edge(edge3)
        self.assertEqual([vert1], list(partition.pre_vertices))
