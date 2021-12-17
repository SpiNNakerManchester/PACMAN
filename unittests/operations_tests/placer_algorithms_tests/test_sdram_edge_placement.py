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
from pacman.model.graphs.machine import (
    MachineGraph, SDRAMMachineEdge)
from pacman.model.graphs.machine import ConstantSDRAMMachinePartition
from pacman.model.resources import ResourceContainer
from pacman.model.routing_info import DictBasedMachinePartitionNKeysMap
from pacman.operations.placer_algorithms import (
    connective_based_placer, one_to_one_placer, radial_placer, spreader_placer)
from pacman_test_objects import MockMachineVertex


class TestSameChipConstraint(unittest.TestCase):

    def setUp(cls):
        unittest_setup()

    def _do_test(self, placer):
        graph = MachineGraph("Test")

        vertices = [
            MockMachineVertex(
                ResourceContainer(), label="v{}".format(i),
                sdram_requirement=20)
            for i in range(100)
        ]
        for vertex in vertices:
            graph.add_vertex(vertex)

        same_vertices = [
            MockMachineVertex(ResourceContainer(), label="same{}".format(i),
                              sdram_requirement=20)
            for i in range(10)
        ]
        random.seed(12345)
        sdram_edges = list()
        for vertex in same_vertices:
            graph.add_vertex(vertex)
            graph.add_outgoing_edge_partition(
                ConstantSDRAMMachinePartition(
                    identifier="Test", pre_vertex=vertex, label="bacon"))
            for _i in range(0, random.randint(1, 5)):
                sdram_edge = SDRAMMachineEdge(
                    vertex, vertices[random.randint(0, 99)], label="bacon",
                    app_edge=None)
                sdram_edges.append(sdram_edge)
                graph.add_edge(sdram_edge, "Test")
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
        for edge in sdram_edges:
            pre_place = placements.get_placement_of_vertex(edge.pre_vertex)
            post_place = placements.get_placement_of_vertex(edge.post_vertex)
            assert pre_place.x == post_place.x
            assert pre_place.y == post_place.y

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
