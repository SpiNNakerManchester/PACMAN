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
from pacman.data.pacman_data_writer import PacmanDataWriter
from pacman.model.partitioner_splitters import SplitterSliceLegacy
from pacman.operations.partition_algorithms import splitter_partitioner
from spinn_machine import (
    SDRAM, Link, Router, Chip, machine_from_chips, virtual_machine)
from pacman.model.graphs.application import ApplicationEdge, ApplicationGraph
from pacman.exceptions import (
    PacmanInvalidParameterException, PacmanValueError)
from pacman.model.constraints.partitioner_constraints import (
     SameAtomsAsVertexConstraint)
from pacman.model.resources import PreAllocatedResourceContainer
from pacman_test_objects import NewPartitionerConstraint, SimpleTestVertex


class TestPartitioner(unittest.TestCase):
    """
    test for partition-and-place partitioning algorithm
    """

    def setUp(self):
        """setup for all basic partitioner tests
        """
        unittest_setup()
        self.vert1 = SimpleTestVertex(10, "New AbstractConstrainedVertex 1")
        self.vert1.splitter = SplitterSliceLegacy()
        self.vert2 = SimpleTestVertex(5, "New AbstractConstrainedVertex 2")
        self.vert2.splitter = SplitterSliceLegacy()
        self.vert3 = SimpleTestVertex(3, "New AbstractConstrainedVertex 3")
        self.vert3.splitter = SplitterSliceLegacy()
        self.edge1 = ApplicationEdge(
            self.vert1, self.vert2, label="First edge")
        self.edge2 = ApplicationEdge(
            self.vert2, self.vert1, label="Second edge")
        self.edge3 = ApplicationEdge(
            self.vert1, self.vert3, label="Third edge")
        self.verts = [self.vert1, self.vert2, self.vert3]
        self.edges = [self.edge1, self.edge2, self.edge3]
        self.graph = ApplicationGraph("Graph")
        self.graph.add_vertices(self.verts)
        self.graph.add_edges(self.edges, "foo")

    def test_partition_with_no_additional_constraints(self):
        """test a partitioning with a graph with no extra constraints
        """
        writer = PacmanDataWriter.mock()
        writer._set_runtime_graph(self.graph)
        writer.set_plan_n_timesteps(100)
        graph, _ = splitter_partitioner(
            pre_allocated_resources=PreAllocatedResourceContainer())
        self.assertEqual(len(list(graph.vertices)), 3)
        vert_sizes = []
        for vert in self.verts:
            vert_sizes.append(vert.n_atoms)
        self.assertEqual(len(list(graph.edges)), 3)
        for vertex in graph.vertices:
            self.assertIn(vertex.vertex_slice.n_atoms, vert_sizes)

    def test_partition_with_no_additional_constraints_extra_edge(self):
        """test that the basic form with an extra edge works
        """
        self.graph.add_edge(
            ApplicationEdge(self.vert3, self.vert1), "TEST")
        writer = PacmanDataWriter.mock()
        writer._set_runtime_graph(self.graph)
        writer.set_plan_n_timesteps(100)
        graph, _ = splitter_partitioner(
            pre_allocated_resources=PreAllocatedResourceContainer())
        self.assertEqual(len(list(graph.vertices)), 3)
        self.assertEqual(len(list(graph.edges)), 4)

    def test_partition_on_large_vertex_than_has_to_be_split(self):
        """
        test that partitioning 1 large vertex can make it into 2 small ones
        """
        large_vertex = SimpleTestVertex(300, "Large vertex")
        large_vertex.splitter = SplitterSliceLegacy()
        self.graph = ApplicationGraph("Graph with large vertex")
        self.graph.add_vertex(large_vertex)
        writer = PacmanDataWriter.mock()
        writer._set_runtime_graph(self.graph)
        writer.set_plan_n_timesteps(100)
        graph, _ = splitter_partitioner(
            pre_allocated_resources=PreAllocatedResourceContainer())
        self.assertEqual(large_vertex._model_based_max_atoms_per_core, 256)
        self.assertGreater(len(list(graph.vertices)), 1)

    def test_partition_on_very_large_vertex_than_has_to_be_split(self):
        """
        test that partitioning 1 large vertex can make it into multiple small
        ones
        """
        large_vertex = SimpleTestVertex(500, "Large vertex")
        large_vertex.splitter = SplitterSliceLegacy()
        self.assertEqual(large_vertex._model_based_max_atoms_per_core, 256)
        self.graph = ApplicationGraph("Graph with large vertex")
        self.graph.add_vertex(large_vertex)
        writer = PacmanDataWriter.mock()
        writer._set_runtime_graph(self.graph)
        writer.set_plan_n_timesteps(100)
        graph, _ = splitter_partitioner(
            pre_allocated_resources=PreAllocatedResourceContainer())
        self.assertEqual(large_vertex._model_based_max_atoms_per_core, 256)
        self.assertGreater(len(list(graph.vertices)), 1)

    def test_partition_on_target_size_vertex_than_has_to_be_split(self):
        """
        test that fixed partitioning causes correct number of vertices
        """
        large_vertex = SimpleTestVertex(
            1000, "Large vertex", max_atoms_per_core=10)
        large_vertex.splitter = SplitterSliceLegacy()
        self.graph = ApplicationGraph("Graph with large vertex")
        self.graph.add_vertex(large_vertex)
        writer = PacmanDataWriter.mock()
        writer._set_runtime_graph(self.graph)
        writer.set_plan_n_timesteps(100)
        graph, _ = splitter_partitioner(
            pre_allocated_resources=PreAllocatedResourceContainer())
        self.assertEqual(len(list(graph.vertices)), 100)

    def test_partition_with_barely_sufficient_space(self):
        """
        test that partitioning will work when close to filling the machine
        """
        n_processors = 18
        (e, ne, n, w, _, _) = range(6)

        links = list()
        links.append(Link(0, 0, e, 0, 1))

        _sdram = SDRAM(2**12)

        links = list()

        links.append(Link(0, 0, e, 1, 1))
        links.append(Link(0, 1, ne, 1, 0))
        links.append(Link(1, 1, n, 0, 0))
        links.append(Link(1, 0, w, 0, 1))
        r = Router(links, False, 1024)

        ip = "192.162.240.253"
        chips = list()
        for x in range(5):
            for y in range(5):
                if x == y == 0:
                    chips.append(Chip(x, y, n_processors, r, _sdram, 0, 0, ip))
                else:
                    chips.append(Chip(x, y, n_processors, r, _sdram, 0, 0))

        PacmanDataWriter.mock().set_machine(machine_from_chips(chips))
        n_neurons = 17 * 5 * 5
        singular_vertex = SimpleTestVertex(n_neurons, "Large vertex",
                                           max_atoms_per_core=1)
        singular_vertex.splitter = SplitterSliceLegacy()
        self.assertEqual(singular_vertex._model_based_max_atoms_per_core, 1)
        self.graph = ApplicationGraph("Graph with large vertex")
        self.graph.add_vertex(singular_vertex)
        writer = PacmanDataWriter.mock()
        writer._set_runtime_graph(self.graph)
        writer.set_plan_n_timesteps(100)
        graph, _ = splitter_partitioner(
            pre_allocated_resources=PreAllocatedResourceContainer())
        self.assertEqual(singular_vertex._model_based_max_atoms_per_core, 1)
        self.assertEqual(len(list(graph.vertices)), n_neurons)

    def test_partition_with_insufficient_space(self):
        """
        test that if there's not enough space, the test the partitioner will
        raise an error
        """
        writer = PacmanDataWriter.mock()
        n_processors = 18
        (e, ne, n, w, _, _) = range(6)

        links = list()
        links.append(Link(0, 0, e, 0, 1))

        _sdram = SDRAM(2**11)

        links = list()

        links.append(Link(0, 0, e, 1, 1))
        links.append(Link(0, 1, ne, 1, 0))
        links.append(Link(1, 1, n, 0, 0))
        links.append(Link(1, 0, w, 0, 1))
        r = Router(links, False, 1024)

        ip = "192.162.240.253"
        chips = list()
        for x in range(5):
            for y in range(5):
                if x == y == 0:
                    chips.append(Chip(x, y, n_processors, r, _sdram, 0, 0, ip))
                else:
                    chips.append(Chip(x, y, n_processors, r, _sdram, 0, 0))

        writer.set_machine(machine_from_chips(chips))
        large_vertex = SimpleTestVertex(3000, "Large vertex",
                                        max_atoms_per_core=1)
        large_vertex.splitter = SplitterSliceLegacy()
        self.assertEqual(large_vertex._model_based_max_atoms_per_core, 1)
        self.graph = ApplicationGraph("Graph with large vertex")
        self.graph.add_vertex(large_vertex)
        writer._set_runtime_graph(self.graph)
        writer.set_plan_n_timesteps(3000)
        with self.assertRaises(PacmanValueError):
            splitter_partitioner(PreAllocatedResourceContainer())

    def test_partition_with_less_sdram_than_default(self):
        """
        test that the partitioner works when its machine is slightly malformed
        in that it has less SDRAM available
        """
        writer = PacmanDataWriter.mock()
        n_processors = 18
        (e, ne, n, w, _, _) = range(6)

        links = list()
        links.append(Link(0, 0, e, 0, 1))

        _sdram = SDRAM(128 * (2**19))

        links = list()

        links.append(Link(0, 0, e, 1, 1))
        links.append(Link(0, 1, ne, 1, 0))
        links.append(Link(1, 1, n, 0, 0))
        links.append(Link(1, 0, w, 0, 1))
        r = Router(links, False, 1024)

        ip = "192.162.240.253"
        chips = list()
        for x in range(5):
            for y in range(5):
                if x == y == 0:
                    chips.append(Chip(x, y, n_processors, r, _sdram, 0, 0, ip))
                else:
                    chips.append(Chip(x, y, n_processors, r, _sdram, 0, 0))

        writer.set_machine(machine_from_chips(chips))
        writer._set_runtime_graph(self.graph)
        writer.set_plan_n_timesteps(3000)
        splitter_partitioner(PreAllocatedResourceContainer())

    def test_partition_with_more_sdram_than_default(self):
        """
        test that the partitioner works when its machine is slightly malformed
        in that it has more SDRAM available
        """
        writer = PacmanDataWriter.mock()
        n_processors = 18
        (e, ne, n, w, _, _) = range(6)

        links = list()
        links.append(Link(0, 0, e, 0, 1))

        _sdram = SDRAM(128 * (2**21))

        links = list()

        links.append(Link(0, 0, e, 1, 1))
        links.append(Link(0, 1, ne, 1, 0))
        links.append(Link(1, 1, n, 0, 0))
        links.append(Link(1, 0, w, 0, 1))
        r = Router(links, False, 1024)

        ip = "192.162.240.253"
        chips = list()
        for x in range(5):
            for y in range(5):
                if x == y == 0:
                    chips.append(Chip(x, y, n_processors, r, _sdram, 0, 0, ip))
                else:
                    chips.append(Chip(x, y, n_processors, r, _sdram, 0, 0))

        writer.set_machine(machine_from_chips(chips))
        writer._set_runtime_graph(self.graph)
        writer.set_plan_n_timesteps(3000)
        splitter_partitioner(PreAllocatedResourceContainer())

    def test_partition_with_unsupported_constraints(self):
        """
        test that when a vertex has a constraint that is unrecognised,
        it raises an error
        """
        constrained_vertex = SimpleTestVertex(13, "Constrained")
        constrained_vertex.add_constraint(
            NewPartitionerConstraint("Mock constraint"))
        with self.assertRaises(PacmanInvalidParameterException):
            constrained_vertex.splitter = SplitterSliceLegacy()

    def test_partition_with_empty_graph(self):
        """test that the partitioner can work with an empty graph
        """
        self.graph = ApplicationGraph("foo")
        writer = PacmanDataWriter.mock()
        writer._set_runtime_graph(self.graph)
        writer.set_plan_n_timesteps(100)
        graph, _ = splitter_partitioner(
            pre_allocated_resources=PreAllocatedResourceContainer())
        self.assertEqual(len(list(graph.vertices)), 0)

    def test_operation_with_same_size_as_vertex_constraint(self):
        """
        test that the partition and place partitioner can handle same size as
        constraints on a vertex that is split into one core
        """
        with self.assertRaises(NotImplementedError):
            constrained_vertex = SimpleTestVertex(5, "Constrained")
            constrained_vertex.add_constraint(
                SameAtomsAsVertexConstraint(self.vert2))
            constrained_vertex.splitter_object = SplitterSliceLegacy()
            self.graph.add_vertex(constrained_vertex)
            writer = PacmanDataWriter.mock()
            writer._set_runtime_graph(self.graph)
            writer.set_plan_n_timesteps(100)
            graph, _ = splitter_partitioner(
                pre_allocated_resources=PreAllocatedResourceContainer())
            self.assertEqual(len(list(graph.vertices)), 4)

    def test_operation_with_same_size_as_vertex_constraint_large_vertices(
            self):
        """
        test that the partition and place partitioner can handle same size as
        constraints on a vertex which has to be split over many cores
        """
        with self.assertRaises(NotImplementedError):
            constrained_vertex = SimpleTestVertex(300, "Constrained")
            new_large_vertex = SimpleTestVertex(300, "Non constrained")
            constrained_vertex.add_constraint(
                SameAtomsAsVertexConstraint(new_large_vertex))
            new_large_vertex.splitter_object = SplitterSliceLegacy()
            constrained_vertex.splitter_object = SplitterSliceLegacy()
            self.graph.add_vertices([new_large_vertex, constrained_vertex])
            writer = PacmanDataWriter.mock()
            writer._set_runtime_graph(self.graph)
            writer.set_plan_n_timesteps(100)
            graph, _ = splitter_partitioner(
                pre_allocated_resources=PreAllocatedResourceContainer())
            self.assertEqual(len(list(graph.vertices)), 7)

    def test_operation_same_size_as_vertex_constraint_different_order(self):
        """
        test that the partition and place partitioner can handle same size as
        constraints on a vertex which has to be split over many cores where
        the order of the vertices being added is different.
        """
        with self.assertRaises(NotImplementedError):
            constrained_vertex = SimpleTestVertex(300, "Constrained")
            new_large_vertex = SimpleTestVertex(300, "Non constrained")
            constrained_vertex.add_constraint(
                SameAtomsAsVertexConstraint(new_large_vertex))
            constrained_vertex.splitter_object = SplitterSliceLegacy()
            new_large_vertex.splitter_object = SplitterSliceLegacy()
            self.graph.add_vertices([constrained_vertex, new_large_vertex])
            writer = PacmanDataWriter.mock()
            writer._set_runtime_graph(self.graph)
            writer.set_plan_n_timesteps(100)
            graph, _ = splitter_partitioner(
                pre_allocated_resources=PreAllocatedResourceContainer())
            # split in 256 each, so 4 machine vertices
            self.assertEqual(len(list(graph.vertices)), 7)

    def test_operation_with_same_size_as_vertex_constraint_chain(self):
        """ Test that a chain of same size constraints works even when the\
            order of vertices is not correct for the chain
        """
        with self.assertRaises(NotImplementedError):
            graph = ApplicationGraph("Test")
            vertex_1 = SimpleTestVertex(10, "Vertex_1", 5)
            vertex_1.splitter_object = SplitterSliceLegacy()
            vertex_2 = SimpleTestVertex(10, "Vertex_2", 4)
            vertex_3 = SimpleTestVertex(10, "Vertex_3", 2)
            vertex_3.add_constraint(SameAtomsAsVertexConstraint(vertex_2))
            vertex_2.add_constraint(SameAtomsAsVertexConstraint(vertex_1))
            vertex_2.splitter_object = SplitterSliceLegacy()
            vertex_3.splitter_object = SplitterSliceLegacy()
            graph.add_vertices([vertex_1, vertex_2, vertex_3])
            writer = PacmanDataWriter.mock()
            writer._set_runtime_graph(graph)
            writer.set_plan_n_timesteps(None)
            splitter_partitioner()
            subvertices_1 = list(vertex_1.machine_vertices)
            subvertices_2 = list(vertex_2.machine_vertices)
            subvertices_3 = list(vertex_3.machine_vertices)
            self.assertEqual(len(subvertices_1), len(subvertices_2))
            self.assertEqual(len(subvertices_2), len(subvertices_3))

    def test_partitioning_with_2_massive_pops(self):
        constrained_vertex = SimpleTestVertex(16000, "Constrained")
        constrained_vertex.splitter = SplitterSliceLegacy()
        self.graph.add_vertex(constrained_vertex)
        constrained_vertex = SimpleTestVertex(16000, "Constrained")
        constrained_vertex.splitter = SplitterSliceLegacy()
        self.graph.add_vertex(constrained_vertex)
        writer = PacmanDataWriter.mock()
        writer._set_runtime_graph(self.graph)
        writer.set_plan_n_timesteps(3000)
        splitter_partitioner(PreAllocatedResourceContainer())

if __name__ == '__main__':
    unittest.main()
