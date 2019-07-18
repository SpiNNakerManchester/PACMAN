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

import random
import unittest
from spinn_machine import virtual_machine
from pacman.model.graphs.machine import MachineGraph, SimpleMachineVertex
from pacman.model.resources import ResourceContainer
from pacman.model.constraints.placer_constraints import SameChipAsConstraint
from pacman.model.routing_info import DictBasedMachinePartitionNKeysMap
from pacman.executor import PACMANAlgorithmExecutor


class TestSameChipConstraint(unittest.TestCase):

    def _do_test(self, placer):
        machine = virtual_machine(width=8, height=8)
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

        n_keys_map = DictBasedMachinePartitionNKeysMap()

        inputs = {
            "MemoryExtendedMachine": machine,
            "MemoryMachine": machine,
            "MemoryMachineGraph": graph,
            "PlanNTimeSteps": None,
            "MemoryMachinePartitionNKeysMap": n_keys_map
        }
        algorithms = [placer]
        xml_paths = []
        executor = PACMANAlgorithmExecutor(
            algorithms, [], inputs, [], [], [], xml_paths)
        executor.execute_mapping()

        placements = executor.get_item("MemoryPlacements")
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
        self._do_test("OneToOnePlacer")

    def test_radial(self):
        self._do_test("RadialPlacer")

    def test_rig(self):
        self._do_test("RigPlace")

    def test_spreader(self):
        self._do_test("SpreaderPlacer")
