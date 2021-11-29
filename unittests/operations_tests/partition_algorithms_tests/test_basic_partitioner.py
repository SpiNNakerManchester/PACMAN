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
test for partitioning
"""

import unittest

from pacman.config_setup import unittest_setup
from pacman.model.partitioner_splitters import SplitterFixedLegacy
from pacman.operations.partition_algorithms import splitter_partitioner
from pacman.model.graphs.application import ApplicationGraph
from pacman.exceptions import PacmanInvalidParameterException
from pacman.model.constraints.partitioner_constraints import (
    MaxVertexAtomsConstraint, FixedVertexAtomsConstraint)
from pacman_test_objects import NewPartitionerConstraint, SimpleTestVertex


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

    def test_partition_with_no_additional_constraints(self):
        """
        test a partitioning with a graph with no extra constraints
        """
        vert1 = SimpleTestVertex(10, "New AbstractConstrainedVertex 1")
        vert1.splitter = SplitterFixedLegacy()
        vert2 = SimpleTestVertex(5, "New AbstractConstrainedVertex 2")
        vert2.splitter = SplitterFixedLegacy()
        vert3 = SimpleTestVertex(3, "New AbstractConstrainedVertex 3")
        vert3.splitter = SplitterFixedLegacy()
        verts = [vert1, vert2, vert3]
        graph = ApplicationGraph("Graph")
        graph.add_vertices(verts)
        splitter_partitioner(graph, 3000)
        self.assertEqual(_n_machine_vertices(graph), 3)
        for vert in verts:
            for m_vert in vert.machine_vertices:
                self.assertEqual(vert.n_atoms, m_vert.vertex_slice.n_atoms)

    def test_partition_on_large_vertex_than_has_to_be_split(self):
        """
        test that partitioning 1 large vertex can make it into 2 small ones
        """
        large_vertex = SimpleTestVertex(300, "Large vertex")
        large_vertex.splitter = SplitterFixedLegacy()
        graph = ApplicationGraph("Graph with large vertex")
        graph.add_vertex(large_vertex)
        self.assertEqual(large_vertex._model_based_max_atoms_per_core, 256)
        splitter_partitioner(graph, 1000)
        self.assertEqual(_n_machine_vertices(graph), 2)

    def test_partition_on_target_size_vertex_than_has_to_be_split(self):
        """
        test that fixed partitioning causes correct number of vertices
        """
        large_vertex = SimpleTestVertex(1000, "Large vertex")
        large_vertex.add_constraint(MaxVertexAtomsConstraint(10))
        large_vertex.splitter = SplitterFixedLegacy()
        graph = ApplicationGraph("Graph with large vertex")
        graph.add_vertex(large_vertex)
        splitter_partitioner(graph, 3000)
        self.assertEqual(_n_machine_vertices(graph), 100)

    def test_partition_with_unsupported_constraints(self):
        """
        test that when a vertex has a constraint that is unrecognised,
        it raises an error
        """
        constrained_vertex = SimpleTestVertex(13, "Constrained")
        constrained_vertex.add_constraint(
            NewPartitionerConstraint("Mock constraint"))
        with self.assertRaises(PacmanInvalidParameterException):
            constrained_vertex.splitter = SplitterFixedLegacy()

    def test_partition_with_empty_graph(self):
        """
        test that the partitioner can work with an empty graph
        """
        graph = ApplicationGraph("foo")
        splitter_partitioner(graph, 3000)
        self.assertEqual(_n_machine_vertices(graph), 0)

    def test_partition_with_fixed_atom_constraints(self):
        """
        test a partitioning with a graph with fixed atom constraint which\
        should fit but is close to the limit
        """

        # Create a vertex which will be split perfectly into 4 cores
        vertex = SimpleTestVertex(
            16, constraints=[FixedVertexAtomsConstraint(4)])
        vertex.splitter = SplitterFixedLegacy()
        app_graph = ApplicationGraph("Test")
        app_graph.add_vertex(vertex)

        # Do the partitioning - this should just work
        partitioner = SplitterPartitioner()
        partitioner(app_graph, 3000)
        self.assertEqual(4, _n_machine_vertices(app_graph))


if __name__ == '__main__':
    unittest.main()
