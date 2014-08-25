import unittest
from pacman.model.partitionable_graph.edge import PartitionedEdge, \
    PartitionedVertex
from pacman.operations.router_algorithms import SteinerTreeWeightedRouting
from pacman.operations.router_algorithms import BasicDijkstraRouting
from pacman.model.partitionable_graph.partitionable_edge import PartitionableEdge
from pacman.model.partitionable_graph.partitionable_graph import PartitionableGraph
from pacman.model.partitioned_graph.partitioned_graph import PartitionedGraph
from pacman.model.placements.placement import Placement
from pacman.model.placements.placements import Placements
from pacman.model.resources.cpu_cycles_per_tick_resource import \
    CPUCyclesPerTickResource
from pacman.model.resources.dtcm_resource import DTCMResource
from pacman.model.resources.resource_container import ResourceContainer
from pacman.model.resources.sdram_resource import SDRAMResource
from pacman.model.routing_info.routing_info import RoutingInfo
from pacman.model.routing_info.subedge_routing_info import SubedgeRoutingInfo
from pacman.operations.router import Router
from spinn_machine.chip import Chip
from spinn_machine.link import Link
from spinn_machine.machine import Machine
from spinn_machine.processor import Processor
from spinn_machine.sdram import SDRAM
from spinn_machine.virutal_machine import VirtualMachine
from pacman.utilities import constants
from pacman.operations.router import Router as pacman_router

from pacman.model.partitionable_graph.abstract_partitionable_vertex import \
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


class TestRouter(unittest.TestCase):
    def setUp(self):
        #sort out graph
        self.vert1 = Vertex(10, "New AbstractConstrainedVertex 1")
        self.vert2 = Vertex(5, "New AbstractConstrainedVertex 2")
        self.edge1 = PartitionableEdge(self.vert1, self.vert2, "First edge")
        self.verts = [self.vert1, self.vert2]
        self.edges = [self.edge1]
        self.graph = PartitionableGraph("Graph", self.verts, self.edges)
        #sort out subgraph
        self.subgraph = PartitionedGraph()
        self.subvert1 = PartitionedVertex(
            0, 10, get_resources_used_by_atoms(0, 10, []))
        self.subvert2 = PartitionedVertex(
            0, 5, get_resources_used_by_atoms(0, 10, []))
        self.subedge = PartitionedEdge(self.subvert1, self.subvert2)
        self.subgraph.add_subvertex(self.subvert1)
        self.subgraph.add_subvertex(self.subvert2)
        self.subgraph.add_subedge(self.subedge)
        #sort out placements
        self.placements = Placements()
        self.placement1 = Placement(x=0, y=0, p=2, subvertex=self.subvert1)
        self.placement2 = Placement(x=1, y=1, p=2, subvertex=self.subvert2)
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
        _sdram = SDRAM(128 * (2 ** 20))
        ip = "192.162.240.253"
        chips = list()
        for x in range(10):
            for y in range(10):
                links = list()

                links.append(Link(x, y, 0, (x + 1)%10, y, n, n))
                links.append(Link(x, y, 1, (x + 1)%10, (y + 1)%10 , s, s))
                links.append(Link(x, y, 2, x, (y + 1)%10, n, n))
                links.append(Link(x, y, 3, (x - 1)%10, y, s, s))
                links.append(Link(x, y, 4, (x - 1)%10, (y - 1)%10, n, n))
                links.append(Link(x, y, 5, x, (y - 1)%10, s, s))

                r = Router(links, False, 100, 1024)
                chips.append(Chip(x, y, processors, r, _sdram, ip))

        self.machine = Machine(chips)

    def test_new_router(self):
        report_folder =  "..\reports"
        self.routing = pacman_router(report_folder=report_folder,
                                     report_states=None)
        self.assertEqual(self.routing._report_folder, report_folder)
        self.assertEqual(self.routing._graph, None)
        self.assertEqual(self.routing.report_states, None)
        self.assertEqual(self.routing._hostname, None)
        self.assertIsInstance(self.routing._router_algorithm,
                              BasicDijkstraRouting)
        self.assertEqual(self.routing._graph_to_subgraph_mappings, None)

    def test_new_router_set_non_default_routing_algorithm(self):
        report_folder =  "..\reports"
        self.routing = pacman_router(
            report_folder=report_folder, report_states=None,
            router_algorithm=SteinerTreeWeightedRouting)
        self.assertEqual(self.routing._report_folder, report_folder)
        self.assertEqual(self.routing._graph, None)
        self.assertEqual(self.routing.report_states, None)
        self.assertEqual(self.routing._hostname, None)
        self.assertIsInstance(self.routing._router_algorithm, SteinerTreeWeightedRouting)
        self.assertEqual(self.routing._graph_to_subgraph_mappings, None)

    def test_run_router(self):
        machine = VirtualMachine(4, 4, False)
        self.routing = pacman_router(report_states=None)
        self.routing.run(
            machine=machine, placements=self.placements,
            partitioned_graph=self.subgraph,
            routing_info_allocation=self.routing_info)


if __name__ == '__main__':
    unittest.main()
