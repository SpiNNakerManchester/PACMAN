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
from collections import deque

from pacman.config_setup import unittest_setup
from pacman.data import PacmanDataView
from pacman.data.pacman_data_writer import PacmanDataWriter
from pacman.model.graphs.machine import MulticastEdgePartition
from pacman.model.graphs.machine import (
    MachineGraph, MachineEdge, SimpleMachineVertex)
from pacman.operations.router_algorithms import basic_dijkstra_routing
from pacman.model.resources import ResourceContainer
from pacman.model.placements import Placements, Placement


class TestBasicDijkstraRouting(unittest.TestCase):

    def setUp(self):
        unittest_setup()

    def test_routing(self):
        writer = PacmanDataWriter.mock()
        graph = MachineGraph("Test")
        machine = PacmanDataView.get_machine()
        placements = Placements()
        vertices = list()

        for chip in machine.chips:
            for processor in chip.processors:
                if not processor.is_monitor:
                    vertex = SimpleMachineVertex(resources=ResourceContainer())
                    graph.add_vertex(vertex)
                    placements.add_placement(Placement(
                        vertex, chip.x, chip.y, processor.processor_id))
                    vertices.append(vertex)

        for vertex in vertices:
            graph.add_outgoing_edge_partition(
                MulticastEdgePartition(
                    identifier="Test", pre_vertex=vertex))
            for vertex_to in vertices:
                if vertex != vertex_to:
                    graph.add_edge(MachineEdge(vertex, vertex_to), "Test")
        writer.set_runtime_machine_graph(graph)
        writer.set_placements(placements)
        routing_paths = basic_dijkstra_routing()

        for vertex in vertices:
            vertices_reached = set()
            queue = deque()
            seen_entries = set()
            placement = placements.get_placement_of_vertex(vertex)
            partition = graph.get_outgoing_edge_partition_starting_at_vertex(
                vertex, "Test")
            entry = routing_paths.get_entry_on_coords_for_edge(
                partition, placement.x, placement.y)
            self.assertEqual(entry.incoming_processor, placement.p)
            queue.append((placement.x, placement.y))
            while len(queue) > 0:
                x, y = queue.pop()
                entry = routing_paths.get_entry_on_coords_for_edge(
                    partition, x, y)
                self.assertIsNotNone(entry)
                chip = machine.get_chip_at(x, y)
                for p in entry.processor_ids:
                    self.assertIsNotNone(chip.get_processor_with_id(p))
                    vertex_found = placements.get_vertex_on_processor(x, y, p)
                    vertices_reached.add(vertex_found)
                seen_entries.add((x, y))
                for link_id in entry.link_ids:
                    link = chip.router.get_link(link_id)
                    self.assertIsNotNone(link)
                    dest_x, dest_y = link.destination_x, link.destination_y
                    if (dest_x, dest_y) not in seen_entries:
                        queue.append((dest_x, dest_y))

            for vertex_to in vertices:
                if vertex != vertex_to:
                    self.assertIn(vertex_to, vertices_reached)


if __name__ == '__main__':
    unittest.main()
