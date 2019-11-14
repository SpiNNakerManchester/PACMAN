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

from __future__ import print_function
from operator import itemgetter
from pprint import pprint as pp
import unittest
from spinn_machine import Chip, Link, Machine, Processor, Router, SDRAM
from pacman.model.graphs.application import ApplicationEdge, ApplicationGraph
from pacman.model.graphs.machine import MachineGraph, SimpleMachineVertex
from pacman.exceptions import PacmanPlaceException
from pacman.model.constraints.placer_constraints import ChipAndCoreConstraint
from pacman.model.graphs.common import GraphMapper
from pacman.operations.placer_algorithms import RadialPlacer
from uinit_test_objects import (
    get_resources_used_by_atoms, T_MachineVertex, T_AppVertex)


class TestRadialPlacer(unittest.TestCase):
    def setUp(self):
        #######################################################################
        # Setting up vertices, edges and graph                                #
        #######################################################################
        self.vert1 = T_AppVertex(100, "New AbstractConstrainedVertex 1")
        self.vert2 = T_AppVertex(5, "New AbstractConstrainedVertex 2")
        self.vert3 = T_AppVertex(3, "New AbstractConstrainedVertex 3")
        self.edge1 = ApplicationEdge(self.vert1, self.vert2, "First edge")
        self.edge2 = ApplicationEdge(self.vert2, self.vert1, "Second edge")
        self.edge3 = ApplicationEdge(self.vert1, self.vert3, "Third edge")
        self.verts = [self.vert1, self.vert2, self.vert3]
        self.edges = [self.edge1, self.edge2, self.edge3]
        self.graph = ApplicationGraph("Graph", self.verts, self.edges)

        #######################################################################
        # Setting up machine                                                  #
        #######################################################################
        flops = 1000
        (_, _, n, _, _, s) = range(6)

        processors = list()
        for i in range(18):
            processors.append(Processor(i, flops))

        _sdram = SDRAM(128*(2**20))

        ip = "192.168.240.253"
        chips = list()
        for x in range(10):
            for y in range(10):
                links = list()

                links.append(Link(x, y, 0, (x + 1) % 10, y))
                links.append(Link(x, y, 1, (x + 1) % 10, (y + 1) % 10))
                links.append(Link(x, y, 2, x, (y + 1) % 10))
                links.append(Link(x, y, 3, (x - 1) % 10, y))
                links.append(Link(x, y, 4, (x - 1) % 10, (y - 1) % 10))
                links.append(Link(x, y, 5, x, (y - 1) % 10))

                r = Router(links, False, 1024)
                chips.append(Chip(x, y, processors, r, _sdram, ip))

        self.machine = Machine(chips)
        #######################################################################
        # Setting up graph and graph_mapper                                   #
        #######################################################################
        self.vertices = list()
        self.vertex1 = T_MachineVertex(
            0, 1, get_resources_used_by_atoms(0, 1, []), "First vertex")
        self.vertex2 = T_MachineVertex(
            1, 5, get_resources_used_by_atoms(1, 5, []), "Second vertex")
        self.vertex3 = T_MachineVertex(
            5, 10, get_resources_used_by_atoms(5, 10, []), "Third vertex")
        self.vertex4 = T_MachineVertex(
            10, 100, get_resources_used_by_atoms(10, 100, []),
            "Fourth vertex")
        self.vertices.append(self.vertex1)
        self.vertices.append(self.vertex2)
        self.vertices.append(self.vertex3)
        self.vertices.append(self.vertex4)
        self.edges = list()
        self.graph = MachineGraph(self.vertices, self.edges)
        self.graph_mapper = GraphMapper()
        self.graph_mapper.add_vertices(self.vertices)

    @unittest.skip("demonstrating skipping")
    def test_new_basic_placer(self):
        self.bp = RadialPlacer(self.machine, self.graph)
        self.assertEqual(self.bp._machine, self.machine)
        self.assertEqual(self.bp._graph, self.graph)

    @unittest.skip("demonstrating skipping")
    def test_place_where_vertices_dont_have_vertex(self):
        self.bp = RadialPlacer(self.machine, self.graph)
        placements = self.bp.place(self.graph, self.graph_mapper)
        for placement in placements.placements:
            print(placement.vertex.label, placement.vertex.n_atoms,
                  'x:', placement.x, 'y:', placement.y, 'p:', placement.p)

    @unittest.skip("demonstrating skipping")
    def test_place_where_vertices_have_vertices(self):
        self.bp = RadialPlacer(self.machine, self.graph)
        self.graph_mapper = GraphMapper()
        self.graph_mapper.add_vertices(self.vertices, self.vert1)
        placements = self.bp.place(self.graph, self.graph_mapper)
        for placement in placements.placements:
            print(placement.vertex.label, placement.vertex.n_atoms,
                  'x:', placement.x, 'y:', placement.y, 'p:', placement.p)

    @unittest.skip("demonstrating skipping")
    def test_place_vertex_too_big_with_vertex(self):
        large_vertex = T_AppVertex(500, "Large vertex 500")
        large_machine_vertex = large_vertex.create_machine_vertex(
            0, 499, get_resources_used_by_atoms(0, 499, []))
        self.graph.add_vertex(large_vertex)
        self.graph = ApplicationGraph("Graph", [large_vertex])
        self.graph_mapper = GraphMapper()
        self.graph_mapper.add_vertices([large_machine_vertex], large_vertex)
        self.bp = RadialPlacer(self.machine, self.graph)
        self.graph = MachineGraph(vertices=[large_machine_vertex])
        with self.assertRaises(PacmanPlaceException):
            self.bp.place(self.graph, self.graph_mapper)

    @unittest.skip("demonstrating skipping")
    def test_try_to_place(self):
        self.assertEqual(True, False, "Test not implemented yet")

    @unittest.skip("demonstrating skipping")
    def test_deal_with_constraint_placement_vertices_dont_have_vertex(self):
        self.bp = RadialPlacer(self.machine, self.graph)
        self.vertex1.add_constraint(ChipAndCoreConstraint(8, 3, 2))
        self.assertIsInstance(self.vertex1.constraints[0],
                              ChipAndCoreConstraint)
        self.vertex2.add_constraint(ChipAndCoreConstraint(3, 5, 7))
        self.vertex3.add_constraint(ChipAndCoreConstraint(2, 4, 6))
        self.vertex4.add_constraint(ChipAndCoreConstraint(6, 4, 16))
        self.vertices = list()
        self.vertices.append(self.vertex1)
        self.vertices.append(self.vertex2)
        self.vertices.append(self.vertex3)
        self.vertices.append(self.vertex4)
        self.edges = list()
        self.graph = MachineGraph(self.vertices, self.edges)
        self.graph_mapper = GraphMapper()
        self.graph_mapper.add_vertices(self.vertices)
        placements = self.bp.place(self.graph, self.graph_mapper)
        for placement in placements.placements:
            print(placement.vertex.label, placement.vertex.n_atoms,
                  'x:', placement.x, 'y:', placement.y, 'p:', placement.p)

    @unittest.skip("demonstrating skipping")
    def test_deal_with_constraint_placement_vertices_have_vertices(self):
        self.bp = RadialPlacer(self.machine, self.graph)
        self.vertex1.add_constraint(ChipAndCoreConstraint(1, 5, 2))
        self.assertIsInstance(self.vertex1.constraints[0],
                              ChipAndCoreConstraint)
        self.vertex2.add_constraint(ChipAndCoreConstraint(3, 5, 7))
        self.vertex3.add_constraint(ChipAndCoreConstraint(2, 4, 6))
        self.vertex4.add_constraint(ChipAndCoreConstraint(6, 7, 16))
        self.vertices = list()
        self.vertices.append(self.vertex1)
        self.vertices.append(self.vertex2)
        self.vertices.append(self.vertex3)
        self.vertices.append(self.vertex4)
        self.edges = list()
        self.graph = MachineGraph(self.vertices, self.edges)
        self.graph_mapper = GraphMapper()
        self.graph_mapper.add_vertices(self.vertices, self.vert1)
        placements = self.bp.place(self.graph, self.graph_mapper)
        for placement in placements.placements:
            print(placement.vertex.label, placement.vertex.n_atoms,
                  'x:', placement.x, 'y:', placement.y, 'p:', placement.p)

    @unittest.skip("demonstrating skipping")
    def test_unsupported_non_placer_constraint(self):
        self.assertEqual(True, False, "Test not implemented yet")

    @unittest.skip("demonstrating skipping")
    def test_unsupported_placer_constraint(self):
        self.assertEqual(True, False, "Test not implemented yet")

    @unittest.skip("demonstrating skipping")
    def test_unsupported_placer_constraints(self):
        self.assertEqual(True, False, "Test not implemented yet")

    @unittest.skip("demonstrating skipping")
    def test_many_vertices(self):
        vertices = list()
        for i in range(20 * 17):  # 51 atoms per each processor on 20 chips
            vertices.append(SimpleMachineVertex(
                0, 50, get_resources_used_by_atoms(0, 50, []),
                "vertex " + str(i)))

        self.graph = ApplicationGraph("Graph", vertices)
        self.graph_mapper = GraphMapper()
        self.graph_mapper.add_vertices(vertices)
        self.bp = RadialPlacer(self.machine, self.graph)
        self.graph = MachineGraph(vertices=vertices)
        placements = self.bp.place(self.graph, self.graph_mapper)

        unorderdered_info = list()
        for placement in placements.placements:
            unorderdered_info.append(
                (placement.vertex.label.split(" ")[0],
                 "{:<4}".format(placement.vertex.label.split(" ")[1]),
                 placement.vertex.n_atoms, 'x: ',
                 placement.x, 'y: ', placement.y, 'p: ', placement.p))

        sorted_info = sorted(unorderdered_info, key=itemgetter(4, 6, 8))
        pp(sorted_info)

        pp("{}".format("=" * 50))
        sorted_info = sorted(unorderdered_info, key=lambda x: int(x[1]))
        pp(sorted_info)

    @unittest.skip("demonstrating skipping")
    def test_too_many_vertices(self):
        vertices = list()
        for i in range(100 * 17):  # 50 atoms per each processor on 20 chips
            vertices.append(SimpleMachineVertex(
                0, 50, get_resources_used_by_atoms(0, 50, []),
                "vertex " + str(i)))

        self.graph = ApplicationGraph("Graph", vertices)
        self.graph_mapper = GraphMapper()
        self.graph_mapper.add_vertices(vertices)
        self.bp = RadialPlacer(self.machine, self.graph)
        self.graph = MachineGraph(vertices=vertices)
        with self.assertRaises(PacmanPlaceException):
            self.bp.place(self.graph, self.graph_mapper)

    @unittest.skip("demonstrating skipping")
    def test_fill_machine(self):
        vertices = list()
        for i in range(99 * 17):  # 50 atoms per each processor on 20 chips
            vertices.append(SimpleMachineVertex(
                0, 50, get_resources_used_by_atoms(0, 50, []),
                "vertex " + str(i)))

        self.graph = ApplicationGraph("Graph", vertices)
        self.graph_mapper = GraphMapper()
        self.graph_mapper.add_vertices(vertices)
        self.bp = RadialPlacer(self.machine, self.graph)
        self.graph = MachineGraph(vertices=vertices)
        self.bp.place(self.graph, self.graph_mapper)


if __name__ == '__main__':
    unittest.main()
