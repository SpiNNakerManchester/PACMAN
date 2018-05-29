from pacman.model.graphs.machine import MachineGraph, SimpleMachineVertex
from spinn_machine import VirtualMachine
from pacman.model.resources import ResourceContainer
from pacman.model.constraints.placer_constraints \
    import SameChipAsConstraint
from pacman.operations.rig_algorithms.rig_place import RigPlace
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
        for vertex in same_vertices:
            graph.add_vertex(vertex)
            for i in range(0, random.randint(1, 5)):
                vertex.add_constraint(
                    SameChipAsConstraint(
                        vertices[random.randint(0, 99)]))

        placements = placer(graph, machine, plan_n_timesteps=None)
        for same in same_vertices:
            print("{0.vertex.label}, {0.x}, {0.y}, {0.p}: {1}".format(
                placements.get_placement_of_vertex(same),
                ["{0.vertex.label}, {0.x}, {0.y}, {0.p}".format(
                    placements.get_placement_of_vertex(constraint.vertex))
                 for constraint in same.constraints]))
            placement = placements.get_placement_of_vertex(same)
            for constraint in same.constraints:
                if isinstance(constraint, SameChipAsConstraint):
                    other_placement = placements.get_placement_of_vertex(
                        constraint.vertex)
                    self.assert_(
                        other_placement.x == placement.x and
                        other_placement.y == placement.y,
                        "Vertex was not placed on the same chip as requested")

    def test_one_to_one(self):
        self._do_test(OneToOnePlacer())

    def test_radial(self):
        self._do_test(RadialPlacer())

    def test_rig(self):
        self._do_test(RigPlace())
