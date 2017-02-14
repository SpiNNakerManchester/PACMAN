# pacman model imports
from pacman.model.graphs.application.impl.application_edge \
    import ApplicationEdge
from pacman.model.graphs.machine.impl.machine_graph import MachineGraph
from pacman.model.graphs.machine.impl.simple_machine_vertex \
    import SimpleMachineVertex
from pacman.model.resources.cpu_cycles_per_tick_resource import \
    CPUCyclesPerTickResource

from pacman.exceptions import PacmanRoutingException
from pacman.model.graphs.application.impl.application_graph \
    import ApplicationGraph
from pacman.model.graphs.machine.impl.machine_edge import MachineEdge
from pacman.model.placements.placement import Placement
from pacman.model.placements.placements import Placements
from pacman.model.resources.dtcm_resource import DTCMResource
from pacman.model.resources.resource_container import ResourceContainer
from pacman.model.resources.sdram_resource import SDRAMResource
from pacman.model.routing_info.partition_routing_info \
    import PartitionRoutingInfo
from pacman.model.routing_info.routing_info import RoutingInfo

# pacman utility imports
from pacman.utilities.constants import DEFAULT_MASK
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

from pacman.model.graphs.application.abstract_application_vertex import \
    AbstractApplicationVertex


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


class Vertex(AbstractApplicationVertex):
    def __init__(self, n_atoms, label):
        AbstractApplicationVertex.__init__(self, label=label, n_atoms=n_atoms,
                                           max_atoms_per_core=256)

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
        self.edge1 = ApplicationEdge(self.vert1, self.vert2, "First edge")
        self.verts = [self.vert1, self.vert2]
        self.edges = [self.edge1]
        self.graph = ApplicationGraph("Graph", self.verts, self.edges)
        # sort out graph
        self.graph = MachineGraph()
        self.vertex1 = SimpleMachineVertex(
            0, 10, get_resources_used_by_atoms(0, 10, []))
        self.vertex2 = SimpleMachineVertex(
            0, 5, get_resources_used_by_atoms(0, 10, []))
        self.edge = MachineEdge(self.vertex1, self.vertex2)
        self.graph.add_vertex(self.vertex1)
        self.graph.add_vertex(self.vertex2)
        self.graph.add_edge(self.edge, "TEST")
        # sort out placements
        self.placements = Placements()
        self.placement1 = Placement(x=0, y=0, p=2, vertex=self.vertex1)
        self.placement2 = Placement(x=1, y=1, p=2, vertex=self.vertex2)
        self.placements.add_placement(self.placement1)
        self.placements.add_placement(self.placement2)
        # sort out routing infos
        self.routing_info = RoutingInfo()
        self.edge_routing_info1 = \
            PartitionRoutingInfo(key=2 << 11, mask=DEFAULT_MASK,
                                 edge=self.edge)
        self.routing_info.add_partition_info(self.edge_routing_info1)
        # create machine
        flops = 1000
        (_, _, n, _, _, s) = range(6)

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

    @unittest.skip("demonstrating skipping")
    def set_up_4_node_board(self):
        flops = 1000
        (_, _, n, _, _, s) = range(6)

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

    @unittest.skip("demonstrating skipping")
    def test_new_basic_router(self):
        dijkstra_router = BasicDijkstraRouting()
        self.assertEqual(dijkstra_router._k, 1)
        self.assertEqual(dijkstra_router._l, 0)
        self.assertEqual(dijkstra_router._m, 0)
        self.assertEqual(dijkstra_router._bw_per_route_entry,
                         dijkstra_router.BW_PER_ROUTE_ENTRY)
        self.assertEqual(dijkstra_router._max_bw, dijkstra_router.MAX_BW)

    @unittest.skip("demonstrating skipping")
    def test_run_basic_routing_off_chip_custom_100_node_machine(self):
        dijkstra_router = BasicDijkstraRouting()
        routing_tables = dijkstra_router.route(
            machine=self.machine, placements=self.placements,
            machine_graph=self.graph,
            routing_info_allocation=self.routing_info)
        for entry in routing_tables.routing_tables:
            print entry.x, entry.y
            for routing_entry in entry.multicast_routing_entries:
                print "\t\tProcessor_ids:{}, Link_ids:{}".format(
                    routing_entry.processor_ids,
                    routing_entry.link_ids)

    @unittest.skip("demonstrating skipping")
    def test_run_basic_routing_off_chip_custom_4_node_machine(self):
        self.set_up_4_node_board()
        dijkstra_router = BasicDijkstraRouting()
        routing_tables = dijkstra_router.route(
            machine=self.machine, placements=self.placements,
            machine_graph=self.graph,
            routing_info_allocation=self.routing_info)

        for entry in routing_tables.routing_tables:
            print entry.x, entry.y
            for routing_entry in entry.multicast_routing_entries:
                print "\t\tProcessor_ids:{}, Link_ids:{}".format(
                    routing_entry.processor_ids,
                    routing_entry.link_ids)

    @unittest.skip("demonstrating skipping")
    def test_bad_machine_setup(self):
        # create machine
        flops = 1000
        (e, _, n, w, _, s) = range(6)

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
                machine_graph=self.graph,
                routing_info_allocation=self.routing_info)

    @unittest.skip("demonstrating skipping")
    def test_routing_on_chip_custom_4_node_machine(self):
        self.placements = Placements()
        self.placement1 = Placement(x=1, y=0, p=2, vertex=self.vertex1)
        self.placement2 = Placement(x=1, y=0, p=3, vertex=self.vertex2)
        self.placements.add_placement(self.placement1)
        self.placements.add_placement(self.placement2)
        # sort out routing infos
        self.routing_info = RoutingInfo()
        self.edge_routing_info1 = \
            PartitionRoutingInfo(key=2 << 11, mask=DEFAULT_MASK,
                                 edge=self.edge)
        self.routing_info.add_partition_info(self.edge_routing_info1)

        self.set_up_4_node_board()

        dijkstra_router = BasicDijkstraRouting()
        routing_tables = dijkstra_router.route(
            machine=self.machine, placements=self.placements,
            machine_graph=self.graph,
            routing_info_allocation=self.routing_info)

        for entry in routing_tables.routing_tables:
            print entry.x, entry.y
            for routing_entry in entry.multicast_routing_entries:
                print "\t\tProcessor_ids:{}, Link_ids:{}".format(
                    routing_entry.processor_ids,
                    routing_entry.link_ids)

    @unittest.skip("demonstrating skipping")
    def test_full_machine_routing(self):
        placements = Placements()
        self.placement1 = Placement(x=1, y=0, p=2, vertex=self.vertex1)
        self.placement2 = Placement(x=1, y=0, p=3, vertex=self.vertex2)
        vertices = list()
        for i in range(4 * 17):  # 51 atoms per each processor on 20 chips
            vertices.append(SimpleMachineVertex(
                0, 50, get_resources_used_by_atoms(0, 50, []),
                "vertex " + str(i)))
        edges = list()
        for i in range(len(vertices)):
            edges.append(MachineEdge(
                vertices[i], vertices[(i + 1) % len(vertices)]))
        graph = MachineGraph(vertices, edges)
        p = 1
        x = 0
        y = 0
        for vertex in vertices:
            placements.add_placement(Placement(vertex, x, y, p))
            p = (p + 1) % 18
            if p == 0:
                p += 1
                y += 1
                if y == 2:
                    y = 0
                    x += 1

        routing_info = RoutingInfo()
        edge_routing_info = list()
        for i in range(len(edges)):
            edge_routing_info.append(PartitionRoutingInfo(
                edges[i], i << 11, DEFAULT_MASK))

        for edge_info in edge_routing_info:
            routing_info.add_partition_info(edge_info)

        self.set_up_4_node_board()

        dijkstra_router = BasicDijkstraRouting()
        routing_tables = dijkstra_router.route(
            machine=self.machine, placements=placements,
            machine_graph=graph,
            routing_info_allocation=routing_info)

        for entry in routing_tables.routing_tables:
            print entry.x, entry.y
            for routing_entry in entry.multicast_routing_entries:
                print "\t\tProcessor_ids:{}, Link_ids:{}".format(
                    routing_entry.processor_ids,
                    routing_entry.link_ids)

    @unittest.skip("demonstrating skipping")
    def test_routing_to_other_machine(self):
        self.assertEqual(True, False, "Test not implemented yet")


if __name__ == '__main__':
    unittest.main()
