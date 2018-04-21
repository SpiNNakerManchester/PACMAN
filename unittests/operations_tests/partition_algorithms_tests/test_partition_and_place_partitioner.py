"""
test for partitioning
"""

# pacman imports
from pacman.model.graphs.application import ApplicationEdge, ApplicationGraph

from pacman.exceptions import PacmanPartitionException, \
    PacmanInvalidParameterException, PacmanValueError
from pacman.model.constraints.partitioner_constraints\
    import MaxVertexAtomsConstraint, MinVertexAtomsConstraint
from pacman.model.constraints.partitioner_constraints\
    import SameAtomsAsVertexConstraint
from pacman.model.resources.pre_allocated_resource_container import \
    PreAllocatedResourceContainer
from pacman.operations.partition_algorithms import PartitionAndPlacePartitioner

# spinnMachine imports
from spinn_machine import Machine, Processor, SDRAM, Link, Router, Chip

# general imports
import unittest
from uinit_test_objects import NewPartitionerConstraint, SimpleTestVertex
from spinn_machine.virtual_machine import VirtualMachine


class TestBasicPartitioner(unittest.TestCase):
    """
    test for basic partitioning algorithm
    """

    def setup(self):
        """setup for all basic partitioner tests
        """
        self.vert1 = SimpleTestVertex(10, "New AbstractConstrainedVertex 1")
        self.vert2 = SimpleTestVertex(5, "New AbstractConstrainedVertex 2")
        self.vert3 = SimpleTestVertex(3, "New AbstractConstrainedVertex 3")
        self.edge1 = ApplicationEdge(self.vert1, self.vert2, None,
                                     "First edge")
        self.edge2 = ApplicationEdge(self.vert2, self.vert1, None,
                                     "Second edge")
        self.edge3 = ApplicationEdge(self.vert1, self.vert3, None,
                                     "Third edge")
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
        self.bp = PartitionAndPlacePartitioner()

    def test_partition_with_no_additional_constraints(self):
        """test a partitioning with a graph with no extra constraints
        """
        self.setup()
        graph, mapper, _ = self.bp(self.graph, self.machine,
                                   PreAllocatedResourceContainer())
        self.assertEqual(len(list(graph.vertices)), 3)
        vert_sizes = []
        for vert in self.verts:
            vert_sizes.append(vert.n_atoms)
        self.assertEqual(len(list(graph.edges)), 3)
        for vertex in graph.vertices:
            self.assertIn(mapper.get_slice(vertex).n_atoms, vert_sizes)

    def test_partition_with_no_additional_constraints_extra_edge(self):
        """test that the basic form with an extra edge works
        """
        self.setup()
        self.graph.add_edge(
            ApplicationEdge(self.vert3, self.vert1), "TEST")
        graph, _, _ = self.bp(self.graph, self.machine,
                              PreAllocatedResourceContainer())
        self.assertEqual(len(list(graph.vertices)), 3)
        self.assertEqual(len(list(graph.edges)), 4)

    def test_partition_on_large_vertex_than_has_to_be_split(self):
        """
        test that partitioning 1 large vertex can make it into 2 small ones
        """
        self.setup()
        large_vertex = SimpleTestVertex(300, "Large vertex")
        self.graph = ApplicationGraph("Graph with large vertex")
        self.graph.add_vertex(large_vertex)
        graph, _, _ = self.bp(self.graph, self.machine,
                              PreAllocatedResourceContainer())
        self.assertEqual(large_vertex._model_based_max_atoms_per_core, 256)
        self.assertGreater(len(list(graph.vertices)), 1)

    def test_partition_on_very_large_vertex_than_has_to_be_split(self):
        """
        test that partitioning 1 large vertex can make it into multiple small
        ones
        """
        self.setup()
        large_vertex = SimpleTestVertex(500, "Large vertex")
        self.assertEqual(large_vertex._model_based_max_atoms_per_core, 256)
        self.graph = ApplicationGraph("Graph with large vertex")
        self.graph.add_vertex(large_vertex)
        graph, _, _ = self.bp(self.graph, self.machine,
                              PreAllocatedResourceContainer())
        self.assertEqual(large_vertex._model_based_max_atoms_per_core, 256)
        self.assertGreater(len(list(graph.vertices)), 1)

    def test_partition_on_target_size_vertex_than_has_to_be_split(self):
        """
        test that fixed partitioning causes correct number of vertices
        """
        self.setup()
        large_vertex = SimpleTestVertex(1000, "Large vertex")
        large_vertex.add_constraint(MaxVertexAtomsConstraint(10))
        self.graph = ApplicationGraph("Graph with large vertex")
        self.graph.add_vertex(large_vertex)
        graph, _, _ = self.bp(self.graph, self.machine,
                              PreAllocatedResourceContainer())
        self.assertEqual(len(list(graph.vertices)), 100)

    def test_partition_with_barely_sufficient_space(self):
        """
        test that partitioning will work when close to filling the machine
        """
        self.setup()
        flops = 200000000
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
        singular_vertex = SimpleTestVertex(450, "Large vertex",
                                           max_atoms_per_core=1)
        self.assertEqual(singular_vertex._model_based_max_atoms_per_core, 1)
        self.graph = ApplicationGraph("Graph with large vertex")
        self.graph.add_vertex(singular_vertex)
        graph, _, _ = self.bp(self.graph, self.machine,
                              PreAllocatedResourceContainer())
        self.assertEqual(singular_vertex._model_based_max_atoms_per_core, 1)
        self.assertEqual(len(list(graph.vertices)), 450)

    def test_partition_with_insufficient_space(self):
        """
        test that if there's not enough space, the test the partitioner will
        raise an error
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
        large_vertex = SimpleTestVertex(3000, "Large vertex",
                                        max_atoms_per_core=1)
        self.assertEqual(large_vertex._model_based_max_atoms_per_core, 1)
        self.graph = ApplicationGraph("Graph with large vertex")
        self.graph.add_vertex(large_vertex)
        with self.assertRaises(PacmanValueError):
            self.bp(self.graph, self.machine, PreAllocatedResourceContainer())

    def test_partition_with_less_sdram_than_default(self):
        """
        test that the partitioner works when its machine is slightly malformed
        in that it has less sdram available
        """
        self.setup()
        flops = 200000000
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
        self.bp(self.graph, self.machine, PreAllocatedResourceContainer())

    def test_partition_with_more_sdram_than_default(self):
        """
        test that the partitioner works when its machine is slightly malformed
        in that it has more sdram available
        """
        self.setup()
        flops = 200000000
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
        self.bp(self.graph, self.machine, PreAllocatedResourceContainer())

    def test_partition_with_unsupported_constraints(self):
        """
        test that when a vertex has a constraint that is unrecognised,
        it raises an error
        """
        self.setup()
        constrained_vertex = SimpleTestVertex(13, "Constrained")
        constrained_vertex.add_constraint(
            NewPartitionerConstraint("Mock constraint"))
        graph = ApplicationGraph("Graph")
        graph.add_vertex(constrained_vertex)
        partitioner = PartitionAndPlacePartitioner()
        with self.assertRaises(PacmanInvalidParameterException):
            partitioner(graph, self.machine, PreAllocatedResourceContainer())

    def test_partition_with_empty_graph(self):
        """test that the partitioner can work with an empty graph
        """
        self.setup()
        self.graph = ApplicationGraph("foo")
        graph, _, _ = self.bp(self.graph, self.machine,
                              PreAllocatedResourceContainer())
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
        self.graph.add_vertex(constrained_vertex)
        partitioner = PartitionAndPlacePartitioner()
        graph, _, _ = partitioner(self.graph, self.machine,
                                  PreAllocatedResourceContainer())
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
        self.graph.add_vertices([new_large_vertex, constrained_vertex])
        partitioner = PartitionAndPlacePartitioner()
        graph, _, _ = partitioner(self.graph, self.machine,
                                  PreAllocatedResourceContainer())
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
        self.graph.add_vertices([constrained_vertex, new_large_vertex])
        partitioner = PartitionAndPlacePartitioner()
        graph, _, _ = partitioner(self.graph, self.machine,
                                  PreAllocatedResourceContainer())
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
        self.graph.add_vertex(constrained_vertex)
        partitioner = PartitionAndPlacePartitioner()
        self.assertRaises(PacmanPartitionException, partitioner,
                          self.graph, self.machine,
                          PreAllocatedResourceContainer())

    def test_operation_with_same_size_as_vertex_constraint_chain(self):
        """ Test that a chain of same size constraints works even when the\
            order of vertices is not correct for the chain
        """
        graph = ApplicationGraph("Test")
        vertex_1 = SimpleTestVertex(10, "Vertex_1", 5)
        vertex_2 = SimpleTestVertex(10, "Vertex_2", 4)
        vertex_3 = SimpleTestVertex(10, "Vertex_3", 2)
        vertex_3.add_constraint(SameAtomsAsVertexConstraint(
            vertex_2))
        vertex_2.add_constraint(SameAtomsAsVertexConstraint(
            vertex_1))
        graph.add_vertices([vertex_1, vertex_2, vertex_3])
        machine = VirtualMachine(version=3, with_wrap_arounds=None)
        partitioner = PartitionAndPlacePartitioner()
        _, graph_mapper, _ = partitioner(graph, machine)
        subvertices_1 = list(graph_mapper.get_machine_vertices(vertex_1))
        subvertices_2 = list(graph_mapper.get_machine_vertices(vertex_2))
        subvertices_3 = list(graph_mapper.get_machine_vertices(vertex_3))
        self.assertEqual(len(subvertices_1), len(subvertices_2))
        self.assertEqual(len(subvertices_2), len(subvertices_3))

    def test_partitioning_with_2_massive_pops(self):
        self.setup()
        constrained_vertex = SimpleTestVertex(16000, "Constrained")
        self.graph.add_vertex(constrained_vertex)
        constrained_vertex = SimpleTestVertex(16000, "Constrained")
        self.graph.add_vertex(constrained_vertex)
        partitioner = PartitionAndPlacePartitioner()
        partitioner(self.graph, self.machine, PreAllocatedResourceContainer())

    @unittest.skip("Test not implemented yet")
    def test_detect_subclass_hierarchy(self):
        self.assertEqual(True, False, "Test not implemented yet")

    @unittest.skip("Test not implemented yet")
    def test_partition_by_atoms(self):
        self.assertEqual(True, False, "Test not implemented yet")

    @unittest.skip("Test not implemented yet")
    def test_scale_down_resource_usage(self):
        self.assertEqual(True, False, "Test not implemented yet")

    @unittest.skip("Test not implemented yet")
    def test_scale_up_resource_usage(self):
        self.assertEqual(True, False, "Test not implemented yet")

    @unittest.skip("Test not implemented yet")
    def test_find_max_ratio(self):
        self.assertEqual(True, False, "Test not implemented yet")

    @unittest.skip("Test not implemented yet")
    def test_locate_vertices_to_partition_now(self):
        self.assertEqual(True, False, "Test not implemented yet")

    @unittest.skip("Test not implemented yet")
    def test_partition_with_supported_constraints_enough_space(self):
        self.assertEqual(True, False, "Test not implemented yet")

    @unittest.skip("Test not implemented yet")
    def test_partition_with_supported_constraints_not_enough_space(self):
        self.assertEqual(True, False, "Test not implemented yet")

    def test_partition_with_min_atom_constraints(self):
        """
        test a partitioning with a graph with min atom constraint
        """

        # Create a 2x2 machine with 10 cores per chip (so 40 cores),
        # but 1MB off 2MB per chip (so 19MB per chip)
        n_cores_per_chip = 10
        sdram_per_chip = (n_cores_per_chip * 2) - 1
        machine = VirtualMachine(
            width=2, height=2, with_monitors=False,
            n_cpus_per_chip=n_cores_per_chip,
            sdram_per_chip=sdram_per_chip)

        # Create a vertex where each atom requires 1MB (default) of SDRAM
        # but which can't be subdivided lower than 2 atoms per core.
        # The vertex has 1 atom per MB of SDRAM, and so would fit but will
        # be disallowed by the min atoms per core constraint
        vertex = SimpleTestVertex(
            sdram_per_chip * machine.n_chips,
            max_atoms_per_core=2, constraints=[MinVertexAtomsConstraint(2)])
        app_graph = ApplicationGraph("Test")
        app_graph.add_vertex(vertex)

        # Do the partitioning - this should result in an error
        with self.assertRaises(PacmanPartitionException):
            partitioner = PartitionAndPlacePartitioner()
            partitioner(app_graph, machine)


if __name__ == '__main__':
    unittest.main()
