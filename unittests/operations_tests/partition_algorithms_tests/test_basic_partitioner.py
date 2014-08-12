import unittest
from pacman.exceptions import PacmanPartitionException
from pacman.operations.partition_algorithms.basic_partitioner \
    import BasicPartitioner
from pacman.model.partitionable_graph.partitionable_graph import PartitionableGraph
from spynnaker.pyNN.models.neural_models.if_curr_exp \
    import IFCurrentExponentialPopulation as Vertex
from pacman.model.partitionable_graph.edge import Edge
from spinn_machine.machine import Machine
from spinn_machine.processor import Processor
from spinn_machine.sdram import SDRAM
from spinn_machine.link import Link
from spinn_machine.router import Router
from spinn_machine.chip import Chip


class TestBasicPartitioner(unittest.TestCase):
    def setUp(self):
        self.vert1 = Vertex(10, "New Vertex 1")
        self.vert2 = Vertex(5, "New Vertex 2")
        self.vert3 = Vertex(3, "New Vertex 3")
        self.edge1 = Edge(self.vert1, self.vert2, "First edge")
        self.edge2 = Edge(self.vert2, self.vert1, "Second edge")
        self.edge3 = Edge(self.vert1, self.vert3, "Third edge")
        self.verts = [self.vert1, self.vert2, self.vert3]
        self.edges = [self.edge1, self.edge2, self.edge3]
        self.graph = PartitionableGraph("Graph", self.verts, self.edges)

        flops = 1000
        (e, ne, n, w, sw, s) = range(6)

        processors = list()
        for i in range(18):
            processors.append(Processor(i, flops))

        links = list()
        links.append(Link(0, 0, 0, 0, 1, s, s))

        _sdram = SDRAM(128*(2**20))

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
                chips.append(Chip(x, y, processors, r, _sdram, ip))

        self.machine = Machine(chips)
        self.bp = BasicPartitioner(1, 600)

    def test_new_basic_partitioner(self):
        self.assertEqual(self.bp._machine_time_step, 1)
        self.assertEqual(self.bp._runtime_in_machine_time_steps, 600)

    def test_partition_with_no_additional_constraints(self):
        self.assertEqual(self.vert1._model_based_max_atoms_per_core, 256)
        subgraph, mapper = self.bp.partition(self.graph,self.machine)
        self.assertEqual(len(subgraph.subvertices), 3)
        vert_sizes = []
        for vert in self.verts:
            vert_sizes.append(vert.n_atoms)
        self.assertEqual(len(subgraph.subedges), 3)
        for subvert in subgraph.subvertices:
            self.assertIn(subvert.n_atoms, vert_sizes)

    def test_partition_with_no_additional_constraints_extra_edge(self):
        self.graph.add_edge(Edge(self.vert3, self.vert1, "Extra edge"))
        subgraph, mapper = self.bp.partition(self.graph,self.machine)
        self.assertEqual(len(subgraph.subvertices), 3)
        self.assertEqual(len(subgraph.subedges), 4)

    def test_partition_on_large_vertex_than_has_to_be_split(self):
        large_vertex = Vertex(300, None, "Large vertex")
        self.assertEqual(large_vertex._model_based_max_atoms_per_core, 256)
        self.graph = PartitionableGraph("Graph with large vertex",
                           [large_vertex],
                           [])
        subgraph, mapper = self.bp.partition(self.graph,self.machine)
        self.assertEqual(large_vertex._model_based_max_atoms_per_core, 256)
        self.assertGreater(len(subgraph.subvertices), 1)
        for subv in subgraph.subvertices:
            print subv.n_atoms, subv.label

    def test_partition_on_very_large_vertex_than_has_to_be_split(self):
        large_vertex = Vertex(500, None, "Large vertex")
        self.assertEqual(large_vertex._model_based_max_atoms_per_core, 256)
        self.graph = PartitionableGraph("Graph with large vertex",
                           [large_vertex],
                           [])
        subgraph, mapper = self.bp.partition(self.graph,self.machine)
        self.assertEqual(large_vertex._model_based_max_atoms_per_core, 256)
        self.assertGreater(len(subgraph.subvertices), 1)
        for subv in subgraph.subvertices:
            print subv.n_atoms, subv.label

    def test_partition_on_target_size_vertex_than_has_to_be_split(self):
        large_vertex = Vertex(1000, None, "Large vertex")
        self.assertEqual(large_vertex._model_based_max_atoms_per_core, 256)
        self.graph = PartitionableGraph("Graph with large vertex",
                           [large_vertex],
                           [])
        subgraph, mapper = self.bp.partition(self.graph,self.machine)
        self.assertEqual(large_vertex._model_based_max_atoms_per_core, 256)
        self.assertGreater(len(subgraph.subvertices), 1)
        for subv in subgraph.subvertices:
            print subv.n_atoms, subv.label

    def test_partition_with_supported_constraints_enough_space(self):
        self.assertEqual(True, False)

    def test_partition_with_supported_constraints_not_enough_space(self):
        self.assertEqual(True, False)


    def test_partition_with_barely_sufficient_space(self):
        flops = 1000
        (e, ne, n, w, sw, s) = range(6)

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
                chips.append(Chip(x, y, processors, r, _sdram, ip))

        self.machine = Machine(chips)
        large_vertex = Vertex(300, None, "Large vertex")
        self.assertEqual(large_vertex._model_based_max_atoms_per_core, 256)
        self.graph = PartitionableGraph("Graph with large vertex",
                           [large_vertex],
                           [])
        subgraph, mapper = self.bp.partition(self.graph,self.machine)
        self.assertEqual(large_vertex._model_based_max_atoms_per_core, 256)
        self.assertEqual(len(subgraph.subvertices), 300)
        for subv in subgraph.subvertices:
            print subv.n_atoms, subv.label

    def test_partition_with_insufficient_space(self):
        flops = 1000
        (e, ne, n, w, sw, s) = range(6)

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
                chips.append(Chip(x, y, processors, r, _sdram, ip))

        self.machine = Machine(chips)
        large_vertex = Vertex(300, None, "Large vertex")
        self.assertEqual(large_vertex._model_based_max_atoms_per_core, 256)
        self.graph = PartitionableGraph("Graph with large vertex",
                           [large_vertex],
                           [])
        with self.assertRaises(PacmanPartitionException):
            self.bp.partition(self.graph,self.machine)

    def test_partition_with_less_sdram_than_default(self):
        flops = 1000
        (e, ne, n, w, sw, s) = range(6)

        processors = list()
        for i in range(18):
            processors.append(Processor(i, flops))

        links = list()
        links.append(Link(0, 0, 0, 0, 1, s, s))

        _sdram = SDRAM(128*(2**19))

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
                chips.append(Chip(x, y, processors, r, _sdram, ip))

        self.machine = Machine(chips)
        subgraph, mapper = self.bp.partition(self.graph,self.machine)

    def test_partition_with_more_sdram_than_default(self):
        flops = 1000
        (e, ne, n, w, sw, s) = range(6)

        processors = list()
        for i in range(18):
            processors.append(Processor(i, flops))

        links = list()
        links.append(Link(0, 0, 0, 0, 1, s, s))

        _sdram = SDRAM(128*(2**21))

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
                chips.append(Chip(x, y, processors, r, _sdram, ip))

        self.machine = Machine(chips)
        subgraph, mapper = self.bp.partition(self.graph,self.machine)

    def test_partition_with_unsupported_constraints(self):
        self.assertEqual(True, False)

    def test_partition_with_empty_graph(self):
        self.graph = PartitionableGraph()
        subgraph, mapper = self.bp.partition(self.graph,self.machine)
        self.assertEqual(len(subgraph.subvertices), 0)



if __name__ == '__main__':
    unittest.main()
