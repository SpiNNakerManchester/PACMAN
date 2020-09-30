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
from __future__ import division
import unittest

from pacman.model.partitioner_splitters import SplitterSliceLegacy
from pacman.operations.partition_algorithms import SplitterPartitioner
from spinn_machine import (
    SDRAM, Link, Router, Chip, machine_from_chips, virtual_machine)
from pacman.model.graphs.application import ApplicationEdge, ApplicationGraph
from pacman.exceptions import (
    PacmanException, PacmanPartitionException, PacmanInvalidParameterException,
    PacmanValueError)
from pacman.model.constraints.partitioner_constraints import (
    MaxVertexAtomsConstraint, FixedVertexAtomsConstraint,
    SameAtomsAsVertexConstraint)
from pacman.model.resources import PreAllocatedResourceContainer
from uinit_test_objects import NewPartitionerConstraint, SimpleTestVertex


class TestPartitionAndPlacePartitioner(unittest.TestCase):
    """
    test for partition-and-place partitioning algorithm
    """

    def setup(self):
        """setup for all basic partitioner tests
        """
        self.vert1 = SimpleTestVertex(10, "New AbstractConstrainedVertex 1")
        self.vert1.splitter_object = SplitterSliceLegacy()
        self.vert2 = SimpleTestVertex(5, "New AbstractConstrainedVertex 2")
        self.vert2.splitter_object = SplitterSliceLegacy()
        self.vert3 = SimpleTestVertex(3, "New AbstractConstrainedVertex 3")
        self.vert3.splitter_object = SplitterSliceLegacy()
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

        n_processors = 18
        (e, ne, n, w, _, _) = range(6)

        links = list()
        links.append(Link(0, 0, e, 0, 1))

        _sdram = SDRAM(128 * (2**20))

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

        self.machine = machine_from_chips(chips)
        self.bp = SplitterPartitioner()

    def test_partition_with_no_additional_constraints(self):
        """test a partitioning with a graph with no extra constraints
        """
        self.setup()
        graph, _ = self.bp(
            self.graph, self.machine, plan_n_time_steps=100,
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
        self.setup()
        self.graph.add_edge(
            ApplicationEdge(self.vert3, self.vert1), "TEST")
        graph, _ = self.bp(
            self.graph, self.machine, plan_n_time_steps=100,
            pre_allocated_resources=PreAllocatedResourceContainer())
        self.assertEqual(len(list(graph.vertices)), 3)
        self.assertEqual(len(list(graph.edges)), 4)

    def test_partition_on_large_vertex_than_has_to_be_split(self):
        """
        test that partitioning 1 large vertex can make it into 2 small ones
        """
        self.setup()
        large_vertex = SimpleTestVertex(300, "Large vertex")
        large_vertex.splitter_object = SplitterSliceLegacy()
        self.graph = ApplicationGraph("Graph with large vertex")
        self.graph.add_vertex(large_vertex)
        graph, _ = self.bp(
            self.graph, self.machine, plan_n_time_steps=100,
            pre_allocated_resources=PreAllocatedResourceContainer())
        self.assertEqual(large_vertex._model_based_max_atoms_per_core, 256)
        self.assertGreater(len(list(graph.vertices)), 1)

    def test_partition_on_very_large_vertex_than_has_to_be_split(self):
        """
        test that partitioning 1 large vertex can make it into multiple small
        ones
        """
        self.setup()
        large_vertex = SimpleTestVertex(500, "Large vertex")
        large_vertex.splitter_object = SplitterSliceLegacy()
        self.assertEqual(large_vertex._model_based_max_atoms_per_core, 256)
        self.graph = ApplicationGraph("Graph with large vertex")
        self.graph.add_vertex(large_vertex)
        graph, _ = self.bp(
            self.graph, self.machine, plan_n_time_steps=100,
            pre_allocated_resources=PreAllocatedResourceContainer())
        self.assertEqual(large_vertex._model_based_max_atoms_per_core, 256)
        self.assertGreater(len(list(graph.vertices)), 1)

    def test_partition_on_target_size_vertex_than_has_to_be_split(self):
        """
        test that fixed partitioning causes correct number of vertices
        """
        self.setup()
        large_vertex = SimpleTestVertex(1000, "Large vertex")
        large_vertex.add_constraint(MaxVertexAtomsConstraint(10))
        large_vertex.splitter_object = SplitterSliceLegacy()
        self.graph = ApplicationGraph("Graph with large vertex")
        self.graph.add_vertex(large_vertex)
        graph, _ = self.bp(
            self.graph, self.machine, plan_n_time_steps=100,
            pre_allocated_resources=PreAllocatedResourceContainer())
        self.assertEqual(len(list(graph.vertices)), 100)

    def test_partition_with_barely_sufficient_space(self):
        """
        test that partitioning will work when close to filling the machine
        """
        self.setup()

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

        self.machine = machine_from_chips(chips)
        n_neurons = 17 * 5 * 5
        singular_vertex = SimpleTestVertex(n_neurons, "Large vertex",
                                           max_atoms_per_core=1)
        singular_vertex.splitter_object = SplitterSliceLegacy()
        self.assertEqual(singular_vertex._model_based_max_atoms_per_core, 1)
        self.graph = ApplicationGraph("Graph with large vertex")
        self.graph.add_vertex(singular_vertex)
        graph, _ = self.bp(
            self.graph, self.machine, plan_n_time_steps=100,
            pre_allocated_resources=PreAllocatedResourceContainer())
        self.assertEqual(singular_vertex._model_based_max_atoms_per_core, 1)
        self.assertEqual(len(list(graph.vertices)), n_neurons)

    def test_partition_with_insufficient_space(self):
        """
        test that if there's not enough space, the test the partitioner will
        raise an error
        """
        self.setup()
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

        self.machine = machine_from_chips(chips)
        large_vertex = SimpleTestVertex(3000, "Large vertex",
                                        max_atoms_per_core=1)
        large_vertex.splitter_object = SplitterSliceLegacy()
        self.assertEqual(large_vertex._model_based_max_atoms_per_core, 1)
        self.graph = ApplicationGraph("Graph with large vertex")
        self.graph.add_vertex(large_vertex)
        with self.assertRaises(PacmanValueError):
            self.bp(self.graph, self.machine, 3000,
                    PreAllocatedResourceContainer())

    def test_partition_with_less_sdram_than_default(self):
        """
        test that the partitioner works when its machine is slightly malformed
        in that it has less SDRAM available
        """
        self.setup()
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

        self.machine = machine_from_chips(chips)
        self.bp(self.graph, self.machine, 3000,
                PreAllocatedResourceContainer())

    def test_partition_with_more_sdram_than_default(self):
        """
        test that the partitioner works when its machine is slightly malformed
        in that it has more SDRAM available
        """
        self.setup()
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

        self.machine = machine_from_chips(chips)
        self.bp(self.graph, self.machine, 3000,
                PreAllocatedResourceContainer())

    def test_partition_with_unsupported_constraints(self):
        """
        test that when a vertex has a constraint that is unrecognised,
        it raises an error
        """
        self.setup()
        constrained_vertex = SimpleTestVertex(13, "Constrained")
        constrained_vertex.add_constraint(
            NewPartitionerConstraint("Mock constraint"))
        with self.assertRaises(PacmanInvalidParameterException):
            constrained_vertex.splitter_object = SplitterSliceLegacy()

    def test_partition_with_empty_graph(self):
        """test that the partitioner can work with an empty graph
        """
        self.setup()
        self.graph = ApplicationGraph("foo")
        graph, _ = self.bp(
            self.graph, self.machine, plan_n_time_steps=100,
            pre_allocated_resources=PreAllocatedResourceContainer())
        self.assertEqual(len(list(graph.vertices)), 0)

    def test_operation_with_same_size_as_vertex_constraint(self):
        """
        test that the partition and place partitioner can handle same size as
        constraints on a vertex that is split into one core
        """
        self.setup()
        constrained_vertex = SimpleTestVertex(5, "Constrained")
        constrained_vertex.add_constraint(
            SameAtomsAsVertexConstraint(self.vert2))
        constrained_vertex.splitter_object = SplitterSliceLegacy()
        self.graph.add_vertex(constrained_vertex)
        graph, _ = self.bp(
            self.graph, self.machine, plan_n_time_steps=100,
            pre_allocated_resources=PreAllocatedResourceContainer())
        self.assertEqual(len(list(graph.vertices)), 4)

    def test_operation_with_same_size_as_vertex_constraint_large_vertices(
            self):
        """
        test that the partition and place partitioner can handle same size as
        constraints on a vertex which has to be split over many cores
        """
        self.setup()
        constrained_vertex = SimpleTestVertex(300, "Constrained")
        new_large_vertex = SimpleTestVertex(300, "Non constrained")
        constrained_vertex.add_constraint(
            SameAtomsAsVertexConstraint(new_large_vertex))
        new_large_vertex.splitter_object = SplitterSliceLegacy()
        constrained_vertex.splitter_object = SplitterSliceLegacy()
        self.graph.add_vertices([new_large_vertex, constrained_vertex])
        graph, _ = self.bp(
            self.graph, self.machine, plan_n_time_steps=100,
            pre_allocated_resources=PreAllocatedResourceContainer())
        self.assertEqual(len(list(graph.vertices)), 7)

    def test_operation_same_size_as_vertex_constraint_different_order(self):
        """
        test that the partition and place partitioner can handle same size as
        constraints on a vertex which has to be split over many cores where
        the order of the vertices being added is different.
        """
        self.setup()
        constrained_vertex = SimpleTestVertex(300, "Constrained")
        new_large_vertex = SimpleTestVertex(300, "Non constrained")
        constrained_vertex.add_constraint(
            SameAtomsAsVertexConstraint(new_large_vertex))
        constrained_vertex.splitter_object = SplitterSliceLegacy()
        new_large_vertex.splitter_object = SplitterSliceLegacy()
        self.graph.add_vertices([constrained_vertex, new_large_vertex])
        graph, _ = self.bp(
            self.graph, self.machine, plan_n_time_steps=100,
            pre_allocated_resources=PreAllocatedResourceContainer())
        # split in 256 each, so 4 machine vertices
        self.assertEqual(len(list(graph.vertices)), 7)

    def test_operation_with_same_size_as_vertex_constraint_exception(self):
        """
        test that a partition same as constraint with different size atoms
        causes errors
        """
        self.setup()
        constrained_vertex = SimpleTestVertex(100, "Constrained")
        constrained_vertex.add_constraint(
            SameAtomsAsVertexConstraint(self.vert2))
        constrained_vertex.splitter_object = SplitterSliceLegacy()
        self.graph.add_vertex(constrained_vertex)
        partitioner = SplitterPartitioner()
        self.assertRaises(PacmanPartitionException, partitioner,
                          self.graph, self.machine, 1000,
                          PreAllocatedResourceContainer())

    def test_operation_with_same_size_as_vertex_constraint_chain(self):
        """ Test that a chain of same size constraints works even when the\
            order of vertices is not correct for the chain
        """
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
        machine = virtual_machine(width=2, height=2)
        partitioner = SplitterPartitioner()
        partitioner(graph, machine, plan_n_time_steps=None)
        subvertices_1 = list(vertex_1.machine_vertices)
        subvertices_2 = list(vertex_2.machine_vertices)
        subvertices_3 = list(vertex_3.machine_vertices)
        self.assertEqual(len(subvertices_1), len(subvertices_2))
        self.assertEqual(len(subvertices_2), len(subvertices_3))

    def test_partitioning_with_2_massive_pops(self):
        self.setup()
        constrained_vertex = SimpleTestVertex(16000, "Constrained")
        constrained_vertex.splitter_object = SplitterSliceLegacy()
        self.graph.add_vertex(constrained_vertex)
        constrained_vertex = SimpleTestVertex(16000, "Constrained")
        constrained_vertex.splitter_object = SplitterSliceLegacy()
        self.graph.add_vertex(constrained_vertex)
        partitioner = SplitterPartitioner()
        partitioner(
            self.graph, self.machine, 3000, PreAllocatedResourceContainer())

    def test_partition_with_fixed_atom_constraints(self):
        """
        test a partitioning with a graph with fixed atom constraint
        """

        # Create a 2x2 machine with 10 cores per chip (so 40 cores),
        # but 1MB off 2MB per chip (so 19MB per chip)
        n_cores_per_chip = 10
        sdram_per_chip = (n_cores_per_chip * 2) - 1
        machine = virtual_machine(
            width=2, height=2, n_cpus_per_chip=n_cores_per_chip,
            sdram_per_chip=sdram_per_chip)

        # Create a vertex where each atom requires 1MB (default) of SDRAM
        # but which can't be subdivided lower than 2 atoms per core.
        # The vertex has 1 atom per MB of SDRAM, and so would fit but will
        # be disallowed by the fixed atoms per core constraint
        vertex = SimpleTestVertex(
            sdram_per_chip * machine.n_chips,
            max_atoms_per_core=2, constraints=[FixedVertexAtomsConstraint(2)])
        vertex.splitter_object = SplitterSliceLegacy()
        app_graph = ApplicationGraph("Test")
        app_graph.add_vertex(vertex)

        # Do the partitioning - this should result in an error
        with self.assertRaises(PacmanException):
            partitioner = SplitterPartitioner()
            partitioner(app_graph, machine, 3000)

    def test_partition_with_fixed_atom_constraints_at_limit(self):
        """
        test a partitioning with a graph with fixed atom constraint which\
        should fit but is close to the limit
        """

        # Create a 2x2 machine with 1 core per chip (so 4 cores),
        # and 8MB SDRAM per chip
        n_cores_per_chip = 2  # remember 1 is the monitor
        sdram_per_chip = 8
        machine = virtual_machine(
            width=2, height=2, n_cpus_per_chip=n_cores_per_chip,
            sdram_per_chip=sdram_per_chip)

        # Create a vertex which will need to be split perfectly into 4 cores
        # to work and which max atoms per core must be ignored
        vertex = SimpleTestVertex(
            sdram_per_chip * 2, max_atoms_per_core=sdram_per_chip,
            constraints=[FixedVertexAtomsConstraint(sdram_per_chip // 2)])
        vertex.splitter_object = SplitterSliceLegacy()
        app_graph = ApplicationGraph("Test")
        app_graph.add_vertex(vertex)

        # Do the partitioning - this should just work
        partitioner = SplitterPartitioner()
        machine_graph, _ = partitioner(app_graph, machine, 3000)
        self.assertEqual(4, len(machine_graph.vertices))


if __name__ == '__main__':
    unittest.main()
