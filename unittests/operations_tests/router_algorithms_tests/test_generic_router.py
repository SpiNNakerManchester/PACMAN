# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import unittest
from spinn_machine import virtual_machine
from pacman.model.graphs.application import (
    ApplicationVertex, ApplicationGraph, ApplicationEdge)
from pacman.model.graphs.machine import (
    MachineEdge, MachineGraph, SimpleMachineVertex)
from pacman.model.placements import Placement, Placements
from pacman.model.routing_info import PartitionRoutingInfo, RoutingInfo
from pacman.operations.router_algorithms import BasicDijkstraRouting
from pacman.utilities.constants import DEFAULT_MASK


class Vertex(ApplicationVertex):
    def __init__(self, n_atoms, label):
        super(Vertex, self).__init__(label=label, max_atoms_per_core=256)
        # Ignoring n_atoms

    def get_cpu_usage_for_atoms(self, lo_atom, hi_atom):
        return 10 * (hi_atom - lo_atom)

    def get_dtcm_usage_for_atoms(self, lo_atom, hi_atom):
        return 200 * (hi_atom - lo_atom)

    def get_sdram_usage_for_atoms(self, lo_atom, hi_atom, vertex_in_edges):
        return 4000 + (50 * (hi_atom - lo_atom))


# noinspection PyProtectedMember
class TestRouter(unittest.TestCase):

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
            0, 10, self.vert1.get_resources_used_by_atoms(0, 10, []))
        self.vertex2 = SimpleMachineVertex(
            0, 5, self.vert2.get_resources_used_by_atoms(0, 10, []))
        self.edge = MachineEdge(self.vertex1, self.vertex2)
        self.graph.add_vertex(self.vertex1)
        self.graph.add_vertex(self.vertex2)
        self.graph.add_edge(self.edge, "TEST")

    @unittest.skip("demonstrating skipping")
    def test_router_with_same_chip_route(self):
        # sort out placements
        self.placements = Placements()
        self.placement1 = Placement(x=0, y=0, p=2, vertex=self.vertex1)
        self.placement2 = Placement(x=0, y=0, p=3, vertex=self.vertex2)
        self.placements.add_placement(self.placement1)
        self.placements.add_placement(self.placement2)
        # sort out routing infos
        self.routing_info = RoutingInfo()
        self.edge_routing_info1 = PartitionRoutingInfo(
            key=2 << 11, mask=DEFAULT_MASK, edge=self.edge)
        self.routing_info.add_partition_info(self.edge_routing_info1)
        # create machine
        self.machine = virtual_machine(10, 10, False)
        self.routing = BasicDijkstraRouting()
        self.routing.route(
            machine=self.machine, placements=self.placements,
            machine_graph=self.graph,
            routing_info_allocation=self.routing_info)

    @unittest.skip("demonstrating skipping")
    def test_router_with_neighbour_chip(self):
        # sort out placements
        self.placements = Placements()
        self.placement1 = Placement(x=0, y=0, p=2, vertex=self.vertex1)
        self.placement2 = Placement(x=1, y=1, p=2, vertex=self.vertex2)
        self.placements.add_placement(self.placement1)
        self.placements.add_placement(self.placement2)
        # sort out routing infos
        self.routing_info = RoutingInfo()
        self.edge_routing_info1 = PartitionRoutingInfo(
            key=2 << 11, mask=DEFAULT_MASK, edge=self.edge)
        self.routing_info.add_partition_info(self.edge_routing_info1)
        # create machine
        self.machine = virtual_machine(10, 10, False)
        self.routing = BasicDijkstraRouting()
        self.routing.route(
            machine=self.machine, placements=self.placements,
            machine_graph=self.graph,
            routing_info_allocation=self.routing_info)

    @unittest.skip("demonstrating skipping")
    def test_router_with_one_hop_route_all_default_link_0(self):
        # sort out placements
        self.placements = Placements()
        self.placement1 = Placement(x=0, y=0, p=2, vertex=self.vertex1)
        self.placement2 = Placement(x=2, y=0, p=2, vertex=self.vertex2)
        self.placements.add_placement(self.placement1)
        self.placements.add_placement(self.placement2)
        # sort out routing infos
        self.routing_info = RoutingInfo()
        self.edge_routing_info1 = PartitionRoutingInfo(
            key=2 << 11, mask=DEFAULT_MASK, edge=self.edge)
        self.routing_info.add_partition_info(self.edge_routing_info1)
        # create machine
        self.machine = virtual_machine(10, 10, False)
        self.routing = BasicDijkstraRouting()
        self.routing.route(
            machine=self.machine, placements=self.placements,
            machine_graph=self.graph,
            routing_info_allocation=self.routing_info)

    @unittest.skip("demonstrating skipping")
    def test_router_with_one_hop_route_all_default_link_1(self):
        self.placements = Placements()
        self.placement1 = Placement(x=0, y=0, p=2, vertex=self.vertex1)
        self.placement2 = Placement(x=2, y=2, p=2, vertex=self.vertex2)
        self.placements.add_placement(self.placement1)
        self.placements.add_placement(self.placement2)
        # sort out routing infos
        self.routing_info = RoutingInfo()
        self.edge_routing_info1 = PartitionRoutingInfo(
            key=2 << 11, mask=DEFAULT_MASK, edge=self.edge)
        self.routing_info.add_partition_info(self.edge_routing_info1)
        # create machine
        self.machine = virtual_machine(10, 10, False)
        self.routing = BasicDijkstraRouting()
        self.routing.route(
            machine=self.machine, placements=self.placements,
            machine_graph=self.graph,
            routing_info_allocation=self.routing_info)

    @unittest.skip("demonstrating skipping")
    def test_router_with_one_hop_route_all_default_link_2(self):
        self.placements = Placements()
        self.placement1 = Placement(x=0, y=0, p=2, vertex=self.vertex1)
        self.placement2 = Placement(x=0, y=2, p=2, vertex=self.vertex2)
        self.placements.add_placement(self.placement1)
        self.placements.add_placement(self.placement2)
        # sort out routing infos
        self.routing_info = RoutingInfo()
        self.edge_routing_info1 = PartitionRoutingInfo(
            key=2 << 11, mask=DEFAULT_MASK, edge=self.edge)
        self.routing_info.add_partition_info(self.edge_routing_info1)
        # create machine
        self.machine = virtual_machine(10, 10, False)
        self.routing = BasicDijkstraRouting()
        self.routing.route(
            machine=self.machine, placements=self.placements,
            machine_graph=self.graph,
            routing_info_allocation=self.routing_info)

    @unittest.skip("demonstrating skipping")
    def test_router_with_one_hop_route_all_default_link_3(self):
        self.placements = Placements()
        self.placement1 = Placement(x=2, y=0, p=2, vertex=self.vertex1)
        self.placement2 = Placement(x=0, y=0, p=2, vertex=self.vertex2)
        self.placements.add_placement(self.placement1)
        self.placements.add_placement(self.placement2)
        # sort out routing infos
        self.routing_info = RoutingInfo()
        self.edge_routing_info1 = PartitionRoutingInfo(
            key=2 << 11, mask=DEFAULT_MASK, edge=self.edge)
        self.routing_info.add_partition_info(self.edge_routing_info1)
        # create machine
        self.machine = virtual_machine(10, 10, False)
        self.routing = BasicDijkstraRouting()
        self.routing.route(
            machine=self.machine, placements=self.placements,
            machine_graph=self.graph,
            routing_info_allocation=self.routing_info)

    @unittest.skip("demonstrating skipping")
    def test_router_with_one_hop_route_all_default_link_4(self):
        self.placements = Placements()
        self.placement1 = Placement(x=2, y=2, p=2, vertex=self.vertex1)
        self.placement2 = Placement(x=0, y=0, p=2, vertex=self.vertex2)
        self.placements.add_placement(self.placement1)
        self.placements.add_placement(self.placement2)
        # sort out routing infos
        self.routing_info = RoutingInfo()
        self.edge_routing_info1 = PartitionRoutingInfo(
            key=2 << 11, mask=DEFAULT_MASK, edge=self.edge)
        self.routing_info.add_partition_info(self.edge_routing_info1)
        # create machine
        self.machine = virtual_machine(10, 10, False)
        self.routing = BasicDijkstraRouting()
        self.routing.route(
            machine=self.machine, placements=self.placements,
            machine_graph=self.graph,
            routing_info_allocation=self.routing_info)

    @unittest.skip("demonstrating skipping")
    def test_router_with_one_hop_route_all_default_link_5(self):
        self.placements = Placements()
        self.placement1 = Placement(x=0, y=2, p=2, vertex=self.vertex1)
        self.placement2 = Placement(x=0, y=0, p=2, vertex=self.vertex2)
        self.placements.add_placement(self.placement1)
        self.placements.add_placement(self.placement2)
        # sort out routing infos
        self.routing_info = RoutingInfo()
        self.edge_routing_info1 = PartitionRoutingInfo(
            key=2 << 11, mask=DEFAULT_MASK, edge=self.edge)
        self.routing_info.add_partition_info(self.edge_routing_info1)
        # create machine
        self.machine = virtual_machine(10, 10, False)
        self.routing = BasicDijkstraRouting()
        self.routing.route(
            machine=self.machine, placements=self.placements,
            machine_graph=self.graph,
            routing_info_allocation=self.routing_info)

    @unittest.skip("demonstrating skipping")
    def test_router_with_one_hop_route_not_default(self):
        # sort out placements
        self.placements = Placements()
        self.placement1 = Placement(x=2, y=1, p=2, vertex=self.vertex1)
        self.placement2 = Placement(x=0, y=0, p=2, vertex=self.vertex2)
        self.placements.add_placement(self.placement1)
        self.placements.add_placement(self.placement2)
        # sort out routing infos
        self.routing_info = RoutingInfo()
        self.edge_routing_info1 = PartitionRoutingInfo(
            key=2 << 11, mask=DEFAULT_MASK, edge=self.edge)
        self.routing_info.add_partition_info(self.edge_routing_info1)
        # create machine
        self.machine = virtual_machine(10, 10, False)
        self.routing = BasicDijkstraRouting()
        self.routing.route(
            machine=self.machine, placements=self.placements,
            machine_graph=self.graph,
            routing_info_allocation=self.routing_info)

    @unittest.skip("demonstrating skipping")
    def test_router_with_multi_hop_route_across_board(self):
        # sort out placements
        self.placements = Placements()
        self.placement1 = Placement(x=0, y=0, p=2, vertex=self.vertex1)
        self.placement2 = Placement(x=8, y=7, p=2, vertex=self.vertex2)
        self.placements.add_placement(self.placement1)
        self.placements.add_placement(self.placement2)
        # sort out routing infos
        self.routing_info = RoutingInfo()
        self.edge_routing_info1 = PartitionRoutingInfo(
            key=2 << 11, mask=DEFAULT_MASK, edge=self.edge)
        self.routing_info.add_partition_info(self.edge_routing_info1)
        # create machine
        self.machine = virtual_machine(10, 10, False)
        self.routing = BasicDijkstraRouting()
        self.routing.route(
            machine=self.machine, placements=self.placements,
            machine_graph=self.graph,
            routing_info_allocation=self.routing_info)

    @unittest.skip("demonstrating skipping")
    def test_new_router(self):
        report_folder = "..\reports"
        self.routing = BasicDijkstraRouting()
        self.assertEqual(self.routing._report_folder, report_folder)
        self.assertEqual(self.routing._graph, None)
        self.assertEqual(self.routing.report_states, None)
        self.assertEqual(self.routing._hostname, None)
        self.assertIsInstance(self.routing._router_algorithm,
                              BasicDijkstraRouting)
        self.assertEqual(self.routing._graph_mappings, None)

    @unittest.skip("demonstrating skipping")
    def test_new_router_set_non_default_routing_algorithm(self):
        report_folder = "..\reports"
        self.routing = BasicDijkstraRouting()
        self.assertEqual(self.routing._report_folder, report_folder)
        self.assertEqual(self.routing._graph, None)
        self.assertEqual(self.routing.report_states, None)
        self.assertEqual(self.routing._hostname, None)
        self.assertEqual(self.routing._graph_mappings, None)

    @unittest.skip("demonstrating skipping")
    def test_run_router(self):
        # sort out placements
        self.placements = Placements()
        self.placement1 = Placement(x=0, y=0, p=2, vertex=self.vertex1)
        self.placement2 = Placement(x=1, y=1, p=2, vertex=self.vertex2)
        self.placements.add_placement(self.placement1)
        self.placements.add_placement(self.placement2)
        # sort out routing infos
        self.routing_info = RoutingInfo()
        self.edge_routing_info1 = PartitionRoutingInfo(
            key=2 << 11, mask=DEFAULT_MASK, edge=self.edge)
        self.routing_info.add_partition_info(self.edge_routing_info1)
        # create machine
        self.machine = virtual_machine(10, 10, False)
        self.routing = BasicDijkstraRouting()
        self.routing.route(
            machine=self.machine, placements=self.placements,
            machine_graph=self.graph,
            routing_info_allocation=self.routing_info)


if __name__ == '__main__':
    unittest.main()
