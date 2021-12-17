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
from pacman.config_setup import unittest_setup
from pacman.data.pacman_data_writer import PacmanDataWriter
from pacman.exceptions import PacmanAlreadyPlacedError
from pacman.model.graphs.machine import MachineGraph, SimpleMachineVertex
from pacman.model.resources import ResourceContainer
from pacman.model.constraints.placer_constraints import SameChipAsConstraint
from pacman.model.routing_info import DictBasedMachinePartitionNKeysMap
from pacman.operations.placer_algorithms import (
    connective_based_placer, one_to_one_placer, radial_placer, spreader_placer)


class TestSameChipConstraint(unittest.TestCase):

    def setUp(self):
        unittest_setup()

    def _do_test(self, placer):
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
            for _i in range(0, random.randint(1, 5)):
                vertex.add_constraint(
                    SameChipAsConstraint(
                        vertices[random.randint(0, 99)]))

        n_keys_map = DictBasedMachinePartitionNKeysMap()

        PacmanDataWriter().set_runtime_machine_graph(graph)
        if placer == "ConnectiveBasedPlacer":
            placements = connective_based_placer(None)
        elif placer == "OneToOnePlacer":
            placements = one_to_one_placer(None)
        elif placer == "RadialPlacer":
            placements = radial_placer(None)
        elif placer == "SpreaderPlacer":
            placements = spreader_placer(n_keys_map, None)
        else:
            raise NotImplementedError(placer)

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
                    self.assertTrue(
                        other_placement.x == placement.x and
                        other_placement.y == placement.y,
                        "Vertex was not placed on the same chip as requested")

    def test_connective_based(self):
        try:
            self._do_test("ConnectiveBasedPlacer")
        except PacmanAlreadyPlacedError:
            raise unittest.SkipTest(
                "https://github.com/SpiNNakerManchester/PACMAN/issues/406")

    def test_one_to_one(self):
        self._do_test("OneToOnePlacer")

    def test_radial(self):
        self._do_test("RadialPlacer")

    def test_spreader(self):
        self._do_test("SpreaderPlacer")
