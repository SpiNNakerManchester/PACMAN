import unittest
from pacman.operations.router_algorithms.basic_dijkstra_routing \
    import BasicDijkstraRouting
from pacman.model.partitionable_graph.abstract_partitionable_vertex import \
    AbstractPartitionableVertex
from unittests.model_tests.test_vertex import TestVertex as Vertex
from pacman.model.partitionable_graph.partitionable_edge import PartitionableEdge
from pacman.model.partitionable_graph.partitionable_graph import PartitionableGraph
from pacman.model.partitioned_graph.partitioned_graph import PartitionedGraph
from spinn_machine.processor import Processor
from spinn_machine.link import Link
from spinn_machine.sdram import SDRAM
from spinn_machine.router import Router
from spinn_machine.chip import Chip
from spinn_machine.machine import Machine

class MyTestCase(unittest.TestCase):

 def setUp(self):
        self.vert1 = Vertex(10, "New Vertex 1")
        self.vert2 = Vertex(5, "New Vertex 2")
        self.edge1 = PartitionableEdge(self.vert1, self.vert2, "First edge")
        self.verts = [self.vert1, self.vert2]
        self.edges = [self.edge1]
        self.graph = PartitionableGraph("Graph", self.verts, self.edges)

        self.subgraph = PartitionedGraph()
        subvert1 = P

        flops = 1000
        (e, ne, n, w, sw, s) = range(6)

        processors = list()
        for i in range(18):
            processors.append(Processor(i, flops))

        links = list()
        links.append(Link(0, 0, 0, 0, 1, s, s))

        _sdram = SDRAM(128 * ( 2 ** 20))

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

    def test_new_basic_routing_over_chip(self):
        self.assertEqual(self.bp._machine_time_step, 1)
        self.assertEqual(self.bp._runtime_in_machine_time_steps, 600)

if __name__ == '__main__':
    unittest.main()