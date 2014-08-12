#pacman model imports
from pacman.model.partitioned_graph.partitioned_edge import PartitionedEdge
from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex
from pacman.model.placements.placement import Placement
from pacman.model.placements.placements import Placements
from pacman.model.routing_info.routing_info import RoutingInfo
from pacman.model.routing_info.subedge_routing_info import SubedgeRoutingInfo
from pacman.model.partitionable_graph.partitionable_edge import PartitionableEdge
from pacman.model.partitionable_graph.partitionable_graph import PartitionableGraph
from pacman.model.partitioned_graph.partitioned_graph import PartitionedGraph
#pacman utility imports
from pacman.utilities import constants
#pacman operations imports
from pacman.operations.router_algorithms.basic_dijkstra_routing \
    import BasicDijkstraRouting
from pacman.operations.router import Router as pacman_router
#unitests imports
from unittests.model_tests.test_vertex import TestVertex as Vertex
#spinnmachine imports
from spinn_machine.processor import Processor
from spinn_machine.link import Link
from spinn_machine.sdram import SDRAM
from spinn_machine.router import Router
from spinn_machine.chip import Chip
from spinn_machine.machine import Machine

import unittest

class MyTestCase(unittest.TestCase):

    def setUp(self):
        #sort out graph
        self.vert1 = Vertex(10, "New Vertex 1")
        self.vert2 = Vertex(5, "New Vertex 2")
        self.edge1 = PartitionableEdge(self.vert1, self.vert2, "First edge")
        self.verts = [self.vert1, self.vert2]
        self.edges = [self.edge1]
        self.graph = PartitionableGraph("Graph", self.verts, self.edges)
        #sort out subgraph
        self.subgraph = PartitionedGraph()
        self.subvert1 = PartitionedVertex(0, 10)
        self.subvert2 = PartitionedVertex(0, 5)
        self.subedge = PartitionedEdge(self.subvert1, self.subvert2)
        self.subgraph.add_subvertex(self.subvert1)
        self.subgraph.add_subvertex(self.subvert2)
        #sort out placements
        self.placements = Placements()
        self.placement1 = Placement(x=0, y=0, p=2, subvertex=self.subvert1)
        self.placement2 = Placement(x=2, y=2, p=2, subvertex=self.subvert2)
        self.placements.add_placement(self.placement1)
        self.placements.add_placement(self.placement2)
        #sort out routing infos
        self.routing_info = RoutingInfo()
        self.subedge_routing_info1 = \
            SubedgeRoutingInfo(key=2 << 11, mask=constants.DEFAULT_MASK,
                               subedge=self.subedge)
        self.routing_info.add_subedge_info(self.subedge_routing_info1)
        #create machine
        flops = 1000
        (e, ne, n, w, sw, s) = range(6)

        processors = list()
        for i in range(18):
            processors.append(Processor(i, flops))

        links = list()
        links.append(Link(0, 0, 0, 0, 1, s, s))

        _sdram = SDRAM(128 * (2 ** 20))

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

    def test_new_basic_routing_over_chip(self):
        self.routing = pacman_router(report_states=None)
        self.routing.run(
            machine=self.machine, placements=self.placements,
            partitioned_graph=self.subgraph,
            routing_info_allocation=self.routing_info)

if __name__ == '__main__':
    unittest.main()