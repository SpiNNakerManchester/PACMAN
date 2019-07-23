import unittest
try:
    from collections.abc import deque
except ImportError:
    from collections import deque
from spinn_machine.virtual_machine import virtual_machine
from pacman.model.graphs.machine import (
    MachineGraph, MachineEdge, SimpleMachineVertex)
from pacman.operations.router_algorithms import BasicDijkstraRouting
from pacman.model.resources import ResourceContainer
from pacman.model.placements import Placements, Placement


class MyTestCase(unittest.TestCase):

    def test_routing(self):
        graph = MachineGraph("Test")
        machine = virtual_machine(2, 2)
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
            for vertex_to in vertices:
                if vertex != vertex_to:
                    graph.add_edge(MachineEdge(vertex, vertex_to), "Test")

        router = BasicDijkstraRouting()
        routing_paths = router.__call__(placements, machine, graph)

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
