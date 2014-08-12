import unittest
from pacman.operations.partition_algorithms.partition_and_place_partitioner \
    import PartitionAndPlacePartitioner
from pacman.operations.placer_algorithms.basic_placer import BasicPlacer
from pacman.exceptions import PacmanPartitionException
from pacman.operations.partition_algorithms.basic_partitioner \
    import BasicPartitioner
from pacman.model.graph.graph import Graph
from spynnaker.pyNN.models.neural_models.if_curr_exp \
    import IFCurrentExponentialPopulation as Vertex
from pacman.model.graph.edge import Edge
from spinn_machine.machine import Machine
from spinn_machine.processor import Processor
from spinn_machine.sdram import SDRAM
from spinn_machine.link import Link
from spinn_machine.router import Router
from spinn_machine.chip import Chip
from pacman.exceptions import PacmanPlaceException

class TestPartitioAndPlacePartitioner(unittest.TestCase):
    def setUp(self):
        self.vert1 = Vertex(10, "New Vertex 1")
        self.vert2 = Vertex(5, "New Vertex 2")
        self.vert3 = Vertex(3, "New Vertex 3")
        self.edge1 = Edge(self.vert1, self.vert2, "First edge")
        self.edge2 = Edge(self.vert2, self.vert1, "Second edge")
        self.edge3 = Edge(self.vert1, self.vert3, "Third edge")
        self.verts = [self.vert1, self.vert2, self.vert3]
        self.edges = [self.edge1, self.edge2, self.edge3]
        self.graph = Graph("Graph", self.verts, self.edges)

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

    def test_new_partitioner(self):
        partitioner = PartitionAndPlacePartitioner(1, 1000)
        self.assertEqual(partitioner._placer_algorithm, None)
        self.assertEqual(partitioner._placement_to_subvert_mapper, dict())

    def test_set_placer_algorithm(self):
        partitioner = PartitionAndPlacePartitioner(1, 1000)
        partitioner.set_placer_algorithm(BasicPlacer, self.machine, self.graph)
        self.assertIsInstance(partitioner._placer_algorithm, BasicPlacer)

    def test_invalid_constraints(self):
        self.assertEqual(True, False)

    def test_update_sdram_allocator(self):
        self.assertEqual(True, False)

    def test_add_vertex_constraints_to_subvertex(self):
        self.assertEqual(True, False)

    def test_generate_sub_edges(self):
        self.assertEqual(True, False)

    def test_get_maximum_resources_per_processor(self):
        self.assertEqual(True, False)

    def test_partition(self):
        with self.assertRaises(PacmanPlaceException):
            partitioner = PartitionAndPlacePartitioner(1, 1000)
            subgraph, graph_to_sub_graph_mapper = \
                partitioner.partition(self.graph, self.machine)

    def test_detect_subclass_hierarchy(self):
        self.assertEqual(True, False)

    def test_partition_by_atoms(self):
        self.assertEqual(True, False)

    def test_partition_vertex(self):
        self.assertEqual(True, False)

    def test_scale_down_resource_usage(self):
        self.assertEqual(True, False)

    def test_scale_up_resource_usage(self):
        self.assertEqual(True, False)

    def test_get_max_atoms_per_core(self):
        self.assertEqual(True, False)

    def test_find_max_ratio(self):
        self.assertEqual(True, False)

    def test_locate_vertices_to_partition_now(self):
        self.assertEqual(True, False)


if __name__ == '__main__':
    unittest.main()
