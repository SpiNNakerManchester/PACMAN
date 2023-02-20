# Copyright (c) 2014 The University of Manchester
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
test for partitioning
"""

import unittest

from pacman.config_setup import unittest_setup
from pacman.data import PacmanDataView
from pacman.model.partitioner_splitters import SplitterFixedLegacy
from pacman.operations.partition_algorithms import splitter_partitioner
from pacman_test_objects import SimpleTestVertex


def _n_machine_vertices(graph):
    return sum([len(v.machine_vertices) for v in graph.vertices])


class TestBasicPartitioner(unittest.TestCase):
    """
    test for basic partitioning algorithm
    """
    # pylint: disable=attribute-defined-outside-init

    TheTestAddress = "192.162.240.253"

    def setUp(self):
        """
        setup for all basic partitioner tests
        """
        unittest_setup()

    def test_partition_with_no_fixed(self):
        """
        test a partitioning with a graph with no fixed_location
        """
        vert1 = SimpleTestVertex(10, "New AbstractConstrainedVertex 1")
        vert1.splitter = SplitterFixedLegacy()
        vert2 = SimpleTestVertex(5, "New AbstractConstrainedVertex 2")
        vert2.splitter = SplitterFixedLegacy()
        vert3 = SimpleTestVertex(3, "New AbstractConstrainedVertex 3")
        vert3.splitter = SplitterFixedLegacy()
        verts = [vert1, vert2, vert3]
        for vert in verts:
            PacmanDataView.add_vertex(vert)
        splitter_partitioner()
        self.assertEqual(PacmanDataView.get_n_machine_vertices(), 3)
        for vert in verts:
            for m_vert in vert.machine_vertices:
                self.assertEqual(vert.n_atoms, m_vert.vertex_slice.n_atoms)

    def test_partition_on_large_vertex_than_has_to_be_split(self):
        """
        test that partitioning 1 large vertex can make it into 2 small ones
        """
        large_vertex = SimpleTestVertex(300, "Large vertex")
        large_vertex.splitter = SplitterFixedLegacy()
        PacmanDataView.add_vertex(large_vertex)
        self.assertEqual(large_vertex._model_based_max_atoms_per_core, 256)
        splitter_partitioner()
        self.assertEqual(PacmanDataView.get_n_machine_vertices(), 2)

    def test_partition_on_target_size_vertex_than_has_to_be_split(self):
        """
        test that fixed partitioning causes correct number of vertices
        """
        large_vertex = SimpleTestVertex(
            1000, "Large vertex", max_atoms_per_core=10)
        large_vertex.splitter = SplitterFixedLegacy()
        PacmanDataView.add_vertex(large_vertex)
        splitter_partitioner()
        self.assertEqual(PacmanDataView.get_n_machine_vertices(), 100)

    def test_partition_with_empty_graph(self):
        """
        test that the partitioner can work with an empty graph
        """
        splitter_partitioner()
        self.assertEqual(PacmanDataView.get_n_machine_vertices(), 0)

    def test_partition_with_fixed_atom(self):
        """
        test a partitioning with a graph with fixed atom constraint which\
        should fit but is close to the limit
        """

        # Create a vertex which will be split perfectly into 4 cores
        vertex = SimpleTestVertex(16, max_atoms_per_core=4)
        vertex.splitter = SplitterFixedLegacy()
        PacmanDataView.add_vertex(vertex)
        # Do the partitioning - this should just work
        splitter_partitioner()
        self.assertEqual(PacmanDataView.get_n_machine_vertices(), 4)


if __name__ == '__main__':
    unittest.main()
