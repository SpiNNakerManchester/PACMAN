"""
test for partitioning
"""

# pacman imports
from pacman.model.graphs.application.impl.application_edge import \
    ApplicationEdge

from pacman.exceptions import PacmanInvalidParameterException, PacmanValueError
from pacman.model.constraints.partitioner_constraints.partitioner_maximum_size_constraint import \
    PartitionerMaximumSizeConstraint
from pacman.model.graphs.application.impl.application_graph \
    import ApplicationGraph
from pacman.operations.partition_algorithms.basic_partitioner \
    import BasicPartitioner

# spinnMachine imports
from spinn_machine.machine import Machine
from spinn_machine.processor import Processor
from spinn_machine.sdram import SDRAM
from spinn_machine.link import Link
from spinn_machine.router import Router
from spinn_machine.chip import Chip

# general imports
import unittest
from uinit_test_objects.test_partitioning_constraint import \
    NewPartitionerConstraint
from uinit_test_objects.test_vertex import TestVertex


class TestBasicPartitioner(unittest.TestCase):
    """
    test for basic parittioning algorithum
    """

    def setup(self):
        """
        setup for all absic partitioner tests
        :return:
        """
        self.vert1 = TestVertex(10, "New AbstractConstrainedVertex 1")
        self.vert2 = TestVertex(5, "New AbstractConstrainedVertex 2")
        self.vert3 = TestVertex(3, "New AbstractConstrainedVertex 3")
        self.edge1 = ApplicationEdge(self.vert1, self.vert2, None, "First edge")
        self.edge2 = ApplicationEdge(self.vert2, self.vert1, None, "Second edge")
        self.edge3 = ApplicationEdge(self.vert1, self.vert3, None, "Third edge")
        self.verts = [self.vert1, self.vert2, self.vert3]
        self.edges = [self.edge1, self.edge2, self.edge3]
        self.graph = ApplicationGraph("Graph")
        self.graph.add_vertices(self.verts)
        self.graph.add_edges(self.edges, "foo")

        flops = 200000000
        (e, _, n, w, _, s) = range(6)

        processors = list()
        for i in range(18):
            processors.append(Processor(i, flops))

        links = list()
        links.append(Link(0, 0, 0, 0, 1, s, s))

        _sdram = SDRAM(128 * (2**20))

        links = list()

        links.append(Link(0, 0, 0, 1, 1, n, n))
        links.append(Link(0, 1, 1, 1, 0, s, s))
        links.append(Link(1, 1, 2, 0, 0, e, e))
        links.append(Link(1, 0, 3, 0, 1, w, w))
        r = Router(links, False, 100, 1024)

        ip = "192.162.240.253"
        chips = list()
        for x in range(5):
            for y in range(5):
                chips.append(Chip(x, y, processors, r, _sdram, 0, 0, ip))

        self.machine = Machine(chips, 0, 0)
        self.bp = BasicPartitioner()

    def test_partition_with_no_additional_constraints(self):
        """
        test a partitionign with a graph with no extra constraints
        :return:
        """
        self.setup()
        graph, mapper, _ = self.bp(self.graph, self.machine)
        self.assertEqual(len(graph.vertices), 3)
        vert_sizes = []
        for vert in self.verts:
            vert_sizes.append(vert.n_atoms)
        self.assertEqual(len(graph.edges), 3)
        for vertex in graph.vertices:
            self.assertIn(mapper.get_slice(vertex).n_atoms, vert_sizes)

    def test_partition_with_no_additional_constraints_extra_edge(self):
        """
        test that the basic form with an extra edge works
        :return:
        """
        self.setup()
        self.graph.add_edge(
            ApplicationEdge(self.vert3, self.vert1, None, "extra"), "TEST")
        graph, _, _ = self.bp(self.graph, self.machine)
        self.assertEqual(len(graph.vertices), 3)
        self.assertEqual(len(graph.edges), 4)

    def test_partition_on_large_vertex_than_has_to_be_split(self):
        """
        test that partitioning 1 lage vertex can make it into 2 small ones
        :return:
        """
        self.setup()
        large_vertex = TestVertex(300, "Large vertex")
        self.graph = ApplicationGraph("Graph with large vertex")
        self.graph.add_vertex(large_vertex)
        self.assertEqual(large_vertex._model_based_max_atoms_per_core, 256)
        graph, _, _ = self.bp(self.graph, self.machine)
        self.assertGreater(len(graph.vertices), 1)

    def test_partition_on_very_large_vertex_than_has_to_be_split(self):
        """
        test that partitioning 1 lage vertex can make it into multiple small ones
        :return:
        """
        self.setup()
        large_vertex = TestVertex(500, "Large vertex")
        self.assertEqual(large_vertex._model_based_max_atoms_per_core, 256)
        self.graph = ApplicationGraph("Graph with large vertex")
        self.graph.add_vertex(large_vertex)
        graph, _, _ = self.bp(self.graph, self.machine)
        self.assertEqual(large_vertex._model_based_max_atoms_per_core, 256)
        self.assertGreater(len(graph.vertices), 1)

    def test_partition_on_target_size_vertex_than_has_to_be_split(self):
        """
        test that fixed partitioning causes correct number of vertices
        :return:
        """
        self.setup()
        large_vertex = TestVertex(1000, "Large vertex")
        large_vertex.add_constraint(PartitionerMaximumSizeConstraint(10))
        self.graph = ApplicationGraph("Graph with large vertex")
        self.graph.add_vertex(large_vertex)
        graph, _, _ = self.bp(self.graph, self.machine)
        self.assertEqual(len(graph.vertices), 100)

    def test_partition_with_barely_sufficient_space(self):
        """
        test that partitioning will work when close to filling the machine
        :return:
        """
        self.setup()
        flops = 1000
        (e, _, n, w, _, s) = range(6)

        processors = list()
        for i in range(18):
            processors.append(Processor(i, flops))

        links = list()
        links.append(Link(0, 0, 0, 0, 1, s, s))

        _sdram = SDRAM(2**12)

        links = list()

        links.append(Link(0, 0, 0, 1, 1, n, n))
        links.append(Link(0, 1, 1, 1, 0, s, s))
        links.append(Link(1, 1, 2, 0, 0, e, e))
        links.append(Link(1, 0, 3, 0, 1, w, w))
        r = Router(links, False, 100, 1024)

        ip = "192.162.240.253"
        chips = list()
        for x in range(5):
            for y in range(5):
                chips.append(Chip(x, y, processors, r, _sdram, 0, 0, ip))

        self.machine = Machine(chips, 0, 0)
        singular_vertex = TestVertex(450, "Large vertex", max_atoms_per_core=1)
        self.assertEqual(singular_vertex._model_based_max_atoms_per_core, 1)
        self.graph = ApplicationGraph("Graph with large vertex")
        self.graph.add_vertex(singular_vertex)
        graph, _, _ = self.bp(self.graph, self.machine)
        self.assertEqual(singular_vertex._model_based_max_atoms_per_core, 1)
        self.assertEqual(len(graph.vertices), 450)

    def test_partition_with_insufficient_space(self):
        """
        test that if theres not enough space, the test the partitioner will
         raise an error
        :return:
        """
        self.setup()
        flops = 1000
        (e, _, n, w, _, s) = range(6)

        processors = list()
        for i in range(18):
            processors.append(Processor(i, flops))

        links = list()
        links.append(Link(0, 0, 0, 0, 1, s, s))

        _sdram = SDRAM(2**11)

        links = list()

        links.append(Link(0, 0, 0, 1, 1, n, n))
        links.append(Link(0, 1, 1, 1, 0, s, s))
        links.append(Link(1, 1, 2, 0, 0, e, e))
        links.append(Link(1, 0, 3, 0, 1, w, w))
        r = Router(links, False, 100, 1024)

        ip = "192.162.240.253"
        chips = list()
        for x in range(5):
            for y in range(5):
                chips.append(Chip(x, y, processors, r, _sdram, 0, 0, ip))

        self.machine = Machine(chips, 0, 0)
        large_vertex = TestVertex(3000, "Large vertex", max_atoms_per_core=1)
        self.assertEqual(large_vertex._model_based_max_atoms_per_core, 1)
        self.graph = ApplicationGraph("Graph with large vertex")
        self.graph.add_vertex(large_vertex)
        with self.assertRaises(PacmanValueError):
            self.bp(self.graph, self.machine)

    def test_partition_with_less_sdram_than_default(self):
        """
        test that the partitioner works when its machine is slightly malformed
        in that it has less sdram avilable
        :return:
        """
        self.setup()
        flops = 1000
        (e, _, n, w, _, s) = range(6)

        processors = list()
        for i in range(18):
            processors.append(Processor(i, flops))

        links = list()
        links.append(Link(0, 0, 0, 0, 1, s, s))

        _sdram = SDRAM(128 * (2**19))

        links = list()

        links.append(Link(0, 0, 0, 1, 1, n, n))
        links.append(Link(0, 1, 1, 1, 0, s, s))
        links.append(Link(1, 1, 2, 0, 0, e, e))
        links.append(Link(1, 0, 3, 0, 1, w, w))
        r = Router(links, False, 100, 1024)

        ip = "192.162.240.253"
        chips = list()
        for x in range(5):
            for y in range(5):
                chips.append(Chip(x, y, processors, r, _sdram, 0, 0, ip))

        self.machine = Machine(chips, 0, 0)
        self.bp(self.graph, self.machine)

    def test_partition_with_more_sdram_than_default(self):
        """
        test that the partitioner works when its machine is slightly malformed
        in that it has more sdram avilable
        :return:
        """
        self.setup()
        flops = 1000
        (e, _, n, w, _, s) = range(6)

        processors = list()
        for i in range(18):
            processors.append(Processor(i, flops))

        links = list()
        links.append(Link(0, 0, 0, 0, 1, s, s))

        _sdram = SDRAM(128 * (2**21))

        links = list()

        links.append(Link(0, 0, 0, 1, 1, n, n))
        links.append(Link(0, 1, 1, 1, 0, s, s))
        links.append(Link(1, 1, 2, 0, 0, e, e))
        links.append(Link(1, 0, 3, 0, 1, w, w))
        r = Router(links, False, 100, 1024)

        ip = "192.162.240.253"
        chips = list()
        for x in range(5):
            for y in range(5):
                chips.append(Chip(x, y, processors, r, _sdram, 0, 0, ip))

        self.machine = Machine(chips, 0, 0)
        self.bp(self.graph, self.machine)

    def test_partition_with_unsupported_constraints(self):
        """
        test that when a vertex has a constraint that is unrecognised,
        it raises an error
        :return:
        """
        self.setup()
        constrained_vertex = TestVertex(13, "Constrained")
        constrained_vertex.add_constraint(
            NewPartitionerConstraint("Mock constraint"))
        graph = ApplicationGraph("Graph")
        self.graph.add_vertex(constrained_vertex)
        partitioner = BasicPartitioner()
        with self.assertRaises(PacmanInvalidParameterException):
            partitioner(graph, self.machine)

    def test_partition_with_empty_graph(self):
        """
        test that the partitioner can work with an empty graph
        :return:
        """
        self.setup()
        self.graph = ApplicationGraph("foo")
        graph, _, _ = self.bp(self.graph, self.machine)
        self.assertEqual(len(graph.vertices), 0)


if __name__ == '__main__':
    unittest.main()
