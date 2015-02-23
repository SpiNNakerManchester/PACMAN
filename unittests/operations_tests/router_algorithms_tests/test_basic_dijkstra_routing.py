# pacman model imports
from pacman.model.resources.cpu_cycles_per_tick_resource import \
    CPUCyclesPerTickResource
from pacman.model.resources.dtcm_resource import DTCMResource
from pacman.model.resources.resource_container import ResourceContainer
from pacman.model.resources.sdram_resource import SDRAMResource
from pacman.exceptions import PacmanRoutingException
from pacman.model.partitioned_graph.partitioned_edge import PartitionedEdge
from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex
from pacman.model.placements.placement import Placement
from pacman.model.placements.placements import Placements
from pacman.model.routing_info.routing_info import RoutingInfo
from pacman.model.routing_info.subedge_routing_info import SubedgeRoutingInfo
from pacman.model.partitionable_graph.partitionable_edge \
    import PartitionableEdge
from pacman.model.partitionable_graph.partitionable_graph \
    import PartitionableGraph
from pacman.model.partitioned_graph.partitioned_graph import PartitionedGraph
# pacman utility imports
from pacman.utilities import constants
# pacman operations imports
from pacman.operations.router_algorithms.basic_dijkstra_routing \
    import BasicDijkstraRouting
# spinnmachine imports
from spinn_machine.processor import Processor
from spinn_machine.link import Link
from spinn_machine.sdram import SDRAM
from spinn_machine.router import Router
from spinn_machine.chip import Chip
from spinn_machine.machine import Machine

import unittest

from pacman.model.abstract_classes.abstract_partitionable_vertex import \
    AbstractPartitionableVertex


def get_resources_used_by_atoms(lo_atom, hi_atom, vertex_in_edges):
    vertex = Vertex(1, None)
    cpu_cycles = vertex.get_cpu_usage_for_atoms(lo_atom, hi_atom)
    dtcm_requirement = vertex.get_dtcm_usage_for_atoms(lo_atom, hi_atom)
    sdram_requirement = \
        vertex.get_sdram_usage_for_atoms(lo_atom, hi_atom, vertex_in_edges)
    # noinspection PyTypeChecker
    resources = ResourceContainer(cpu=CPUCyclesPerTickResource(cpu_cycles),
                                  dtcm=DTCMResource(dtcm_requirement),
                                  sdram=SDRAMResource(sdram_requirement))
    return resources


class Vertex(AbstractPartitionableVertex):
    def __init__(self, n_atoms, label):
        AbstractPartitionableVertex.__init__(self, label=label, n_atoms=n_atoms,
                                             max_atoms_per_core=256)

    def model_name(self):
        return "test vertex"

    def get_cpu_usage_for_atoms(self, lo_atom, hi_atom):
        return 10 * (hi_atom - lo_atom)

    def get_dtcm_usage_for_atoms(self, lo_atom, hi_atom):
        return 200 * (hi_atom - lo_atom)

    def get_sdram_usage_for_atoms(self, lo_atom, hi_atom, vertex_in_edges):
        return 4000 + (50 * (hi_atom - lo_atom))


class MyTestCase(unittest.TestCase):
    def setUp(self):
        # sort out graph
        self.vert1 = Vertex(10, "New AbstractConstrainedVertex 1")
        self.vert2 = Vertex(5, "New AbstractConstrainedVertex 2")
        self.edge1 = PartitionableEdge(self.vert1, self.vert2, "First edge")
        self.verts = [self.vert1, self.vert2]
        self.edges = [self.edge1]
        self.graph = PartitionableGraph("Graph", self.verts, self.edges)
        # sort out subgraph
        self.subgraph = PartitionedGraph()
        self.subvert1 = PartitionedVertex(
            0, 10, get_resources_used_by_atoms(0, 10, []))
        self.subvert2 = PartitionedVertex(
            0, 5, get_resources_used_by_atoms(0, 10, []))
        self.subedge = PartitionedEdge(self.subvert1, self.subvert2)
        self.subgraph.add_subvertex(self.subvert1)
        self.subgraph.add_subvertex(self.subvert2)
        self.subgraph.add_subedge(self.subedge)
        # sort out placements
        self.placements = Placements()
        self.placement1 = Placement(x=0, y=0, p=2, subvertex=self.subvert1)
        self.placement2 = Placement(x=1, y=1, p=2, subvertex=self.subvert2)
        self.placements.add_placement(self.placement1)
        self.placements.add_placement(self.placement2)
        # sort out routing infos
        self.routing_info = RoutingInfo()
        self.subedge_routing_info1 = \
            SubedgeRoutingInfo(key=2 << 11, mask=constants.DEFAULT_MASK,
                               subedge=self.subedge)
        self.routing_info.add_subedge_info(self.subedge_routing_info1)
        # create machine
        flops = 1000
        (e, ne, n, w, sw, s) = range(6)

        processors = list()
        for i in range(18):
            processors.append(Processor(i, flops))
        _sdram = SDRAM(128 * (2 ** 20))
        ip = "192.162.240.253"
        chips = list()
        for x in range(10):
            for y in range(10):
                links = list()

                links.append(Link(x, y, 0, (x + 1) % 10, y, n, n))
                links.append(Link(x, y, 1, (x + 1) % 10, (y + 1) % 10, s, s))
                links.append(Link(x, y, 2, x, (y + 1) % 10, n, n))
                links.append(Link(x, y, 3, (x - 1) % 10, y, s, s))
                links.append(Link(x, y, 4, (x - 1) % 10, (y - 1) % 10, n, n))
                links.append(Link(x, y, 5, x, (y - 1) % 10, s, s))

                r = Router(links, False, 100, 1024)
                chips.append(Chip(x, y, processors, r, _sdram, ip))

        self.machine = Machine(chips)

    def set_up_4_node_board(self):
        flops = 1000
        (e, ne, n, w, sw, s) = range(6)

        processors = list()
        for i in range(18):
            processors.append(Processor(i, flops))
        _sdram = SDRAM(128 * (2 ** 20))
        ip = "192.162.240.253"
        chips = list()
        for x in range(2):
            for y in range(2):
                links = list()

                links.append(Link(x, y, 0, (x + 1) % 2, y, n, n))
                links.append(Link(x, y, 1, (x + 1) % 2, (y + 1) % 2, s, s))
                links.append(Link(x, y, 2, x, (y + 1) % 2, n, n))
                links.append(Link(x, y, 3, (x - 1) % 2, y, s, s))
                links.append(Link(x, y, 4, (x - 1) % 2, (y - 1) % 2, n, n))
                links.append(Link(x, y, 5, x, (y - 1) % 2, s, s))

                r = Router(links, False, 100, 1024)
                chips.append(Chip(x, y, processors, r, _sdram, ip))

        self.machine = Machine(chips)

    def test_new_basic_router(self):
        dijkstra_router = BasicDijkstraRouting()
        self.assertEqual(dijkstra_router._k, 1)
        self.assertEqual(dijkstra_router._l, 0)
        self.assertEqual(dijkstra_router._m, 0)
        self.assertEqual(dijkstra_router._bw_per_route_entry,
                         dijkstra_router.BW_PER_ROUTE_ENTRY)
        self.assertEqual(dijkstra_router._max_bw, dijkstra_router.MAX_BW)

    def test_run_basic_routing_off_chip_custom_100_node_machine(self):
        dijkstra_router = BasicDijkstraRouting()
        routing_tables = dijkstra_router.route(
            machine=self.machine, placements=self.placements,
            partitioned_graph=self.subgraph,
            routing_info_allocation=self.routing_info)
        for entry in routing_tables.routing_tables:
            print entry.x, entry.y
            for routing_entry in entry.multicast_routing_entries:
                print "\t\tProcessor_ids:{}, Link_ids:{}".format(
                    routing_entry.processor_ids,
                    routing_entry.link_ids)

    def test_run_basic_routing_off_chip_custom_4_node_machine(self):
        self.set_up_4_node_board()
        dijkstra_router = BasicDijkstraRouting()
        routing_tables = dijkstra_router.route(
            machine=self.machine, placements=self.placements,
            partitioned_graph=self.subgraph,
            routing_info_allocation=self.routing_info)

        for entry in routing_tables.routing_tables:
            print entry.x, entry.y
            for routing_entry in entry.multicast_routing_entries:
                print "\t\tProcessor_ids:{}, Link_ids:{}".format(
                    routing_entry.processor_ids,
                    routing_entry.link_ids)

    def test_bad_machine_setup(self):
        # create machine
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
        dijkstra_router = BasicDijkstraRouting()

        with self.assertRaises(PacmanRoutingException):
            dijkstra_router.route(
                machine=self.machine, placements=self.placements,
                partitioned_graph=self.subgraph,
                routing_info_allocation=self.routing_info)

    def test_routing_on_chip_custom_4_node_machine(self):
        self.placements = Placements()
        self.placement1 = Placement(x=1, y=0, p=2, subvertex=self.subvert1)
        self.placement2 = Placement(x=1, y=0, p=3, subvertex=self.subvert2)
        self.placements.add_placement(self.placement1)
        self.placements.add_placement(self.placement2)
        # sort out routing infos
        self.routing_info = RoutingInfo()
        self.subedge_routing_info1 = \
            SubedgeRoutingInfo(key=2 << 11, mask=constants.DEFAULT_MASK,
                               subedge=self.subedge)
        self.routing_info.add_subedge_info(self.subedge_routing_info1)

        self.set_up_4_node_board()

        dijkstra_router = BasicDijkstraRouting()
        routing_tables = dijkstra_router.route(
            machine=self.machine, placements=self.placements,
            partitioned_graph=self.subgraph,
            routing_info_allocation=self.routing_info)

        for entry in routing_tables.routing_tables:
            print entry.x, entry.y
            for routing_entry in entry.multicast_routing_entries:
                print "\t\tProcessor_ids:{}, Link_ids:{}".format(
                    routing_entry.processor_ids,
                    routing_entry.link_ids)

    def test_full_machine_routing(self):
        placements = Placements()
        self.placement1 = Placement(x=1, y=0, p=2, subvertex=self.subvert1)
        self.placement2 = Placement(x=1, y=0, p=3, subvertex=self.subvert2)
        subvertices = list()
        for i in range(4 * 17): #51 atoms per each processor on 20 chips
            subvertices.append(PartitionedVertex(
                0, 50, get_resources_used_by_atoms(0, 50, []),
                "Subvertex " + str(i)))
        subedges = list()
        for i in range(len(subvertices)):
            subedges.append(PartitionedEdge(
                subvertices[i], subvertices[(i + 1)%len(subvertices)]))
        subgraph = PartitionedGraph("Subgraph", subvertices, subedges)
        p = 1
        x = 0
        y = 0
        for subvert in subvertices:
            placements.add_placement(Placement(subvert, x, y, p))
            p = (p + 1) % 18
            if p == 0:
                p += 1
                y += 1
                if y == 2:
                    y = 0
                    x += 1

        routing_info = RoutingInfo()
        subedge_routing_info = list()
        for i in range(len(subedges)):
            subedge_routing_info.append(SubedgeRoutingInfo(
                subedges[i], i<<11, constants.DEFAULT_MASK))

        for subedge_info in subedge_routing_info:
            routing_info.add_subedge_info(subedge_info)


        self.set_up_4_node_board()

        dijkstra_router = BasicDijkstraRouting()
        routing_tables = dijkstra_router.route(
            machine=self.machine, placements=placements,
            partitioned_graph=subgraph,
            routing_info_allocation=routing_info)

        for entry in routing_tables.routing_tables:
            print entry.x, entry.y
            for routing_entry in entry.multicast_routing_entries:
                print "\t\tProcessor_ids:{}, Link_ids:{}".format(
                    routing_entry.processor_ids,
                    routing_entry.link_ids)

    def test_routing_to_other_machine(self):
        self.assertEqual(True, False, "Test not implemented yet")


if __name__ == '__main__':
    unittest.main()