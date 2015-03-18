import unittest

from pacman.model.partitioned_graph.abstract_partitioned_edge import \
    AbstractPartitionedEdge
from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex
from pacman.operations.router_algorithms import SteinerTreeWeightedRouting
from pacman.operations.router_algorithms import BasicDijkstraRouting
from pacman.model.partitionable_graph.abstract_partitionable_edge \
    import AbstractPartitionableEdge
from pacman.model.partitionable_graph.partitionable_graph \
    import PartitionableGraph
from pacman.model.partitioned_graph.partitioned_graph import PartitionedGraph
from pacman.model.placements.placement import Placement
from pacman.model.placements.placements import Placements
from pacman.model.routing_info.routing_info import RoutingInfo
from pacman.model.routing_info.subedge_routing_info import SubedgeRoutingInfo
from spinn_machine.virutal_machine import VirtualMachine
from pacman.utilities import constants
from pacman.model.abstract_classes.abstract_partitionable_vertex import \
    AbstractPartitionableVertex


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


# noinspection PyProtectedMember
class TestRouter(unittest.TestCase):

    def setUp(self):
        #sort out graph
        self.vert1 = Vertex(10, "New AbstractConstrainedVertex 1")
        self.vert2 = Vertex(5, "New AbstractConstrainedVertex 2")
        self.edge1 = AbstractPartitionableEdge(self.vert1, self.vert2, "First edge")
        self.verts = [self.vert1, self.vert2]
        self.edges = [self.edge1]
        self.graph = PartitionableGraph("Graph", self.verts, self.edges)
        #sort out subgraph
        self.subgraph = PartitionedGraph()
        self.subvert1 = PartitionedVertex(
            0, 10, self.vert1.get_resources_used_by_atoms(0, 10, []))
        self.subvert2 = PartitionedVertex(
            0, 5, self.vert2.get_resources_used_by_atoms(0, 10, []))
        self.subedge = AbstractPartitionedEdge(self.subvert1, self.subvert2)
        self.subgraph.add_subvertex(self.subvert1)
        self.subgraph.add_subvertex(self.subvert2)
        self.subgraph.add_subedge(self.subedge)

    def test_router_with_same_chip_route(self):
        #sort out placements
        self.placements = Placements()
        self.placement1 = Placement(x=0, y=0, p=2, subvertex=self.subvert1)
        self.placement2 = Placement(x=0, y=0, p=3, subvertex=self.subvert2)
        self.placements.add_placement(self.placement1)
        self.placements.add_placement(self.placement2)
        #sort out routing infos
        self.routing_info = RoutingInfo()
        self.subedge_routing_info1 = \
            SubedgeRoutingInfo(key=2 << 11, mask=constants.DEFAULT_MASK,
                               subedge=self.subedge)
        self.routing_info.add_subedge_info(self.subedge_routing_info1)
        #create machine
        self.machine = VirtualMachine(10, 10, False)
        self.routing = BasicDijkstraRouting()
        self.routing.route(
            machine=self.machine, placements=self.placements,
            partitioned_graph=self.subgraph,
            routing_info_allocation=self.routing_info)

    def test_router_with_neighbour_chip(self):
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
        self.machine = VirtualMachine(10, 10, False)
        self.routing = BasicDijkstraRouting()
        self.routing.route(
            machine=self.machine, placements=self.placements,
            partitioned_graph=self.subgraph,
            routing_info_allocation=self.routing_info)

    def test_router_with_one_hop_route_all_default_link_0(self):
        #sort out placements
        self.placements = Placements()
        self.placement1 = Placement(x=0, y=0, p=2, subvertex=self.subvert1)
        self.placement2 = Placement(x=2, y=0, p=2, subvertex=self.subvert2)
        self.placements.add_placement(self.placement1)
        self.placements.add_placement(self.placement2)
        #sort out routing infos
        self.routing_info = RoutingInfo()
        self.subedge_routing_info1 = \
            SubedgeRoutingInfo(key=2 << 11, mask=constants.DEFAULT_MASK,
                               subedge=self.subedge)
        self.routing_info.add_subedge_info(self.subedge_routing_info1)
        #create machine
        self.machine = VirtualMachine(10, 10, False)
        self.routing = BasicDijkstraRouting()
        self.routing.route(
            machine=self.machine, placements=self.placements,
            partitioned_graph=self.subgraph,
            routing_info_allocation=self.routing_info)

    def test_router_with_one_hop_route_all_default_link_1(self):
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
        self.machine = VirtualMachine(10, 10, False)
        self.routing = BasicDijkstraRouting()
        self.routing.route(
            machine=self.machine, placements=self.placements,
            partitioned_graph=self.subgraph,
            routing_info_allocation=self.routing_info)

    def test_router_with_one_hop_route_all_default_link_2(self):
        self.placements = Placements()
        self.placement1 = Placement(x=0, y=0, p=2, subvertex=self.subvert1)
        self.placement2 = Placement(x=0, y=2, p=2, subvertex=self.subvert2)
        self.placements.add_placement(self.placement1)
        self.placements.add_placement(self.placement2)
        #sort out routing infos
        self.routing_info = RoutingInfo()
        self.subedge_routing_info1 = \
            SubedgeRoutingInfo(key=2 << 11, mask=constants.DEFAULT_MASK,
                               subedge=self.subedge)
        self.routing_info.add_subedge_info(self.subedge_routing_info1)
        #create machine
        self.machine = VirtualMachine(10, 10, False)
        self.routing = BasicDijkstraRouting()
        self.routing.route(
            machine=self.machine, placements=self.placements,
            partitioned_graph=self.subgraph,
            routing_info_allocation=self.routing_info)

    def test_router_with_one_hop_route_all_default_link_3(self):
        self.placements = Placements()
        self.placement1 = Placement(x=2, y=0, p=2, subvertex=self.subvert1)
        self.placement2 = Placement(x=0, y=0, p=2, subvertex=self.subvert2)
        self.placements.add_placement(self.placement1)
        self.placements.add_placement(self.placement2)
        #sort out routing infos
        self.routing_info = RoutingInfo()
        self.subedge_routing_info1 = \
            SubedgeRoutingInfo(key=2 << 11, mask=constants.DEFAULT_MASK,
                               subedge=self.subedge)
        self.routing_info.add_subedge_info(self.subedge_routing_info1)
        #create machine
        self.machine = VirtualMachine(10, 10, False)
        self.routing = BasicDijkstraRouting()
        self.routing.route(
            machine=self.machine, placements=self.placements,
            partitioned_graph=self.subgraph,
            routing_info_allocation=self.routing_info)

    def test_router_with_one_hop_route_all_default_link_4(self):
        self.placements = Placements()
        self.placement1 = Placement(x=2, y=2, p=2, subvertex=self.subvert1)
        self.placement2 = Placement(x=0, y=0, p=2, subvertex=self.subvert2)
        self.placements.add_placement(self.placement1)
        self.placements.add_placement(self.placement2)
        #sort out routing infos
        self.routing_info = RoutingInfo()
        self.subedge_routing_info1 = \
            SubedgeRoutingInfo(key=2 << 11, mask=constants.DEFAULT_MASK,
                               subedge=self.subedge)
        self.routing_info.add_subedge_info(self.subedge_routing_info1)
        #create machine
        self.machine = VirtualMachine(10, 10, False)
        self.routing = BasicDijkstraRouting()
        self.routing.route(
            machine=self.machine, placements=self.placements,
            partitioned_graph=self.subgraph,
            routing_info_allocation=self.routing_info)

    def test_router_with_one_hop_route_all_default_link_5(self):
        self.placements = Placements()
        self.placement1 = Placement(x=0, y=2, p=2, subvertex=self.subvert1)
        self.placement2 = Placement(x=0, y=0, p=2, subvertex=self.subvert2)
        self.placements.add_placement(self.placement1)
        self.placements.add_placement(self.placement2)
        #sort out routing infos
        self.routing_info = RoutingInfo()
        self.subedge_routing_info1 = \
            SubedgeRoutingInfo(key=2 << 11, mask=constants.DEFAULT_MASK,
                               subedge=self.subedge)
        self.routing_info.add_subedge_info(self.subedge_routing_info1)
        #create machine
        self.machine = VirtualMachine(10, 10, False)
        self.routing = BasicDijkstraRouting()
        self.routing.route(
            machine=self.machine, placements=self.placements,
            partitioned_graph=self.subgraph,
            routing_info_allocation=self.routing_info)

    def test_router_with_one_hop_route_not_default(self):
        #sort out placements
        self.placements = Placements()
        self.placement1 = Placement(x=2, y=1, p=2, subvertex=self.subvert1)
        self.placement2 = Placement(x=0, y=0, p=2, subvertex=self.subvert2)
        self.placements.add_placement(self.placement1)
        self.placements.add_placement(self.placement2)
        #sort out routing infos
        self.routing_info = RoutingInfo()
        self.subedge_routing_info1 = \
            SubedgeRoutingInfo(key=2 << 11, mask=constants.DEFAULT_MASK,
                               subedge=self.subedge)
        self.routing_info.add_subedge_info(self.subedge_routing_info1)
        #create machine
        self.machine = VirtualMachine(10, 10, False)
        self.routing = BasicDijkstraRouting()
        self.routing.route(
            machine=self.machine, placements=self.placements,
            partitioned_graph=self.subgraph,
            routing_info_allocation=self.routing_info)

    def test_router_with_multi_hop_route_across_board(self):
        #sort out placements
        self.placements = Placements()
        self.placement1 = Placement(x=0, y=0, p=2, subvertex=self.subvert1)
        self.placement2 = Placement(x=8, y=7, p=2, subvertex=self.subvert2)
        self.placements.add_placement(self.placement1)
        self.placements.add_placement(self.placement2)
        #sort out routing infos
        self.routing_info = RoutingInfo()
        self.subedge_routing_info1 = \
            SubedgeRoutingInfo(key=2 << 11, mask=constants.DEFAULT_MASK,
                               subedge=self.subedge)
        self.routing_info.add_subedge_info(self.subedge_routing_info1)
        #create machine
        self.machine = VirtualMachine(10, 10, False)
        self.routing = BasicDijkstraRouting()
        self.routing.route(
            machine=self.machine, placements=self.placements,
            partitioned_graph=self.subgraph,
            routing_info_allocation=self.routing_info)

    def test_new_router(self):
        report_folder = "..\reports"
        self.routing = BasicDijkstraRouting()
        self.assertEqual(self.routing._report_folder, report_folder)
        self.assertEqual(self.routing._graph, None)
        self.assertEqual(self.routing.report_states, None)
        self.assertEqual(self.routing._hostname, None)
        self.assertIsInstance(self.routing._router_algorithm,
                              BasicDijkstraRouting)
        self.assertEqual(self.routing._graph_to_subgraph_mappings, None)

    def test_new_router_set_non_default_routing_algorithm(self):
        report_folder = "..\reports"
        self.routing = BasicDijkstraRouting()
        self.assertEqual(self.routing._report_folder, report_folder)
        self.assertEqual(self.routing._graph, None)
        self.assertEqual(self.routing.report_states, None)
        self.assertEqual(self.routing._hostname, None)
        self.assertIsInstance(self.routing._router_algorithm,
                              SteinerTreeWeightedRouting)
        self.assertEqual(self.routing._graph_to_subgraph_mappings, None)

    def test_run_router(self):
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
        self.machine = VirtualMachine(10, 10, False)
        self.routing = BasicDijkstraRouting()
        self.routing.route(
            machine=self.machine, placements=self.placements,
            partitioned_graph=self.subgraph,
            routing_info_allocation=self.routing_info)

if __name__ == '__main__':
    unittest.main()
