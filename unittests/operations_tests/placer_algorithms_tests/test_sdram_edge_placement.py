from pacman.model.graphs.machine import MachineGraph, SimpleMachineVertex
from spinn_machine import VirtualMachine
from pacman.model.resources import ResourceContainer
from pacman.model.graphs.machine.machine_edge import MachineEdge
from pacman.model.graphs.common.edge_traffic_type import EdgeTrafficType
from pacman.operations.placer_algorithms.one_to_one_placer \
    import OneToOnePlacer
from pacman.operations.placer_algorithms import RadialPlacer
import random
import unittest


class TestSameChipConstraint(unittest.TestCase):

    def _do_test(self, placer):
        machine = VirtualMachine(width=8, height=8)
        graph = MachineGraph("Test")

        vertices = [
            SimpleMachineVertex(ResourceContainer(), label="v{}".format(i))
            for i in range(100)
        ]
        for vertex in vertices:
            graph.add_vertex(vertex)

        same_vertices = [
            SimpleMachineVertex(ResourceContainer(), label="same{}".format(i))
            for i in range(10)
        ]
        random.seed(12345)
        sdram_edges = list()
        for vertex in same_vertices:
            graph.add_vertex(vertex)
            for i in range(0, random.randint(1, 5)):
                sdram_edge = MachineEdge(
                    vertex, vertices[random.randint(0, 99)],
                    traffic_type=EdgeTrafficType.SDRAM)
                sdram_edges.append(sdram_edge)
                graph.add_edge(sdram_edge, "Test")

        placements = placer(graph, machine)
        for edge in sdram_edges:
            pre_place = placements.get_placement_of_vertex(edge.pre_vertex)
            post_place = placements.get_placement_of_vertex(edge.post_vertex)
            assert pre_place.x == post_place.x
            assert pre_place.y == post_place.y

    def test_one_to_one(self):
        self._do_test(OneToOnePlacer())

    def test_radial(self):
        self._do_test(RadialPlacer())
