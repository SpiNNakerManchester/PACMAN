from spinn_machine import virtual_machine
from pacman.model.graphs.machine import MachineGraph, SimpleMachineVertex
from pacman.model.resources import ResourceContainer
from pacman.model.graphs.machine.machine_edge import MachineEdge
from pacman.model.graphs.common.edge_traffic_type import EdgeTrafficType
from pacman.model.routing_info import DictBasedMachinePartitionNKeysMap
from pacman.executor.pacman_algorithm_executor import PACMANAlgorithmExecutor
import random
import unittest


class TestSameChipConstraint(unittest.TestCase):

    def _do_test(self, placer):
        machine = virtual_machine(width=8, height=8)
        graph = MachineGraph("Test")
        plan_n_timesteps = 100

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
        n_keys_map = DictBasedMachinePartitionNKeysMap()

        inputs = {
            "MemoryExtendedMachine": machine,
            "MemoryMachine": machine,
            "MemoryMachineGraph": graph,
            "PlanNTimeSteps": plan_n_timesteps,
            "MemoryMachinePartitionNKeysMap": n_keys_map
        }
        algorithms = [placer]
        xml_paths = []
        executor = PACMANAlgorithmExecutor(
            algorithms, [], inputs, [], [], [], xml_paths)
        executor.execute_mapping()
        placements = executor.get_item("MemoryPlacements")
        for edge in sdram_edges:
            pre_place = placements.get_placement_of_vertex(edge.pre_vertex)
            post_place = placements.get_placement_of_vertex(edge.post_vertex)
            assert pre_place.x == post_place.x
            assert pre_place.y == post_place.y

    def test_one_to_one(self):
        self._do_test("OneToOnePlacer")

    def test_radial(self):
        self._do_test("RadialPlacer")

    def test_rig(self):
        self._do_test("RigPlace")

    def test_spreader(self):
        self._do_test("SpreaderPlacer")
