# Copyright (c) 2022 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
from typing import Optional, cast
from typing_extensions import Self
from spinn_utilities.config_holder import set_config
from pacman.config_setup import unittest_setup
from pacman.data.pacman_data_writer import PacmanDataWriter
from pacman.model.graphs.application import ApplicationEdge
from pacman.model.graphs.machine import SimpleMachineVertex
from pacman.model.partitioner_splitters import SplitterFixedLegacy
from pacman.model.placements import Placement, Placements
from pacman.model.resources import ConstantSDRAM
from pacman.operations.placer_algorithms import place_application_graph
from pacman.operations.partition_algorithms import splitter_partitioner
from pacman.operations.router_algorithms.application_router import (
    route_application_graph)
from pacman.operations.routing_info_allocator_algorithms import (
    ZonedRoutingInfoAllocator)
from pacman.operations.routing_table_generators import (
    basic_routing_table_generator)
from pacman_test_objects import SimpleTestVertex
from pacman.model.graphs.application.abstract import (
    AbstractOneAppOneMachineVertex)
from pacman.model.routing_info.base_key_and_mask import BaseKeyAndMask
from pacman.model.partitioner_splitters import SplitterOneAppOneMachine


class FixedKeyAppVertex(AbstractOneAppOneMachineVertex):

    def __init__(
            self, fixed_key_and_mask: Optional[BaseKeyAndMask],
            label: Optional[str] = None,
            n_atoms: int = 1):
        AbstractOneAppOneMachineVertex.__init__(
            self, SimpleMachineVertex(ConstantSDRAM(1000)), label,
            n_atoms=n_atoms)
        self.__fixed_key_and_mask = fixed_key_and_mask
        self._splitter = SplitterOneAppOneMachine()
        self._splitter.set_governed_app_vertex(cast(Self, self))

    def get_fixed_key_and_mask(
            self, partition_id: str) -> Optional[BaseKeyAndMask]:
        return self.__fixed_key_and_mask


class TestBasic(unittest.TestCase):

    def setUp(self) -> None:
        unittest_setup()
        # TODO check after
        #  https://github.com/SpiNNakerManchester/PACMAN/pull/555
        set_config("Machine", "version", "5")

    def create_graphs3(self, writer: PacmanDataWriter) -> None:
        v1 = SimpleTestVertex(
            300, "app1", max_atoms_per_core=10, splitter=SplitterFixedLegacy())
        v2 = SimpleTestVertex(
            300, "app2", max_atoms_per_core=10, splitter=SplitterFixedLegacy())
        v3 = SimpleTestVertex(
            10, "app3", max_atoms_per_core=10, splitter=SplitterFixedLegacy())
        v4 = SimpleTestVertex(
            10, "app4", max_atoms_per_core=10, splitter=SplitterFixedLegacy())
        writer.add_vertex(v1)
        writer.add_vertex(v2)
        writer.add_vertex(v3)
        writer.add_vertex(v4)
        writer.add_edge(ApplicationEdge(v1, v2), "foo")
        writer.add_edge(ApplicationEdge(v3, v4), "foo")
        writer.add_edge(ApplicationEdge(v1, v3), "foo")
        writer.add_edge(ApplicationEdge(v2, v4), "foo")
        writer.add_edge(ApplicationEdge(v1, v1), "foo")

    def make_infos(self, writer: PacmanDataWriter,
                   system_placements: Optional[Placements] = None) -> None:
        if system_placements is None:
            system_placements = Placements()
        splitter_partitioner()
        writer.set_placements(place_application_graph(system_placements))
        writer.set_routing_table_by_partition(route_application_graph())
        allocator = ZonedRoutingInfoAllocator()
        writer.set_routing_infos(allocator.allocate([]))

    def test_empty(self) -> None:
        writer = PacmanDataWriter.mock()
        self.make_infos(writer)
        data = basic_routing_table_generator()
        self.assertEqual(0, data.get_max_number_of_entries())
        self.assertEqual(0, len(list(data.routing_tables)))

    def test_graph3_with_system(self) -> None:
        writer = PacmanDataWriter.mock()
        self.create_graphs3(writer)
        system_plaements = Placements()
        mv = SimpleMachineVertex(ConstantSDRAM(1))
        system_plaements.add_placement(Placement(mv, 1, 2, 3))
        self.make_infos(writer, system_plaements)
        data = basic_routing_table_generator()
        self.assertEqual(31, data.get_max_number_of_entries())
        self.assertEqual(108, data.get_total_number_of_entries())
        self.assertEqual(5, len(list(data.routing_tables)))

    def test_overlapping(self) -> None:
        # Two vertices in the same router can't send with the same key
        writer = PacmanDataWriter.mock()
        v_target = SimpleTestVertex(1, splitter=SplitterFixedLegacy())
        v1 = FixedKeyAppVertex(BaseKeyAndMask(0x1, 0xFFFFFFFF))
        v2 = FixedKeyAppVertex(BaseKeyAndMask(0x1, 0xFFFFFFFF))
        writer.add_vertex(v_target)
        writer.add_vertex(v1)
        writer.add_vertex(v2)
        writer.add_edge(ApplicationEdge(v1, v_target), "Test")
        writer.add_edge(ApplicationEdge(v2, v_target), "Test")
        system_placements = Placements()
        system_placements.add_placement(Placement(v1.machine_vertex, 0, 0, 1))
        system_placements.add_placement(Placement(v2.machine_vertex, 0, 0, 2))
        self.make_infos(writer, system_placements)
        with self.assertRaises(KeyError):
            basic_routing_table_generator()

    def test_overlapping_different_chips(self) -> None:
        # Two vertices in the same router can't send with the same key
        writer = PacmanDataWriter.mock()
        v_target = SimpleTestVertex(1, splitter=SplitterFixedLegacy())
        v1 = FixedKeyAppVertex(BaseKeyAndMask(0x1, 0xFFFFFFFF))
        v2 = FixedKeyAppVertex(BaseKeyAndMask(0x1, 0xFFFFFFFF))
        writer.add_vertex(v_target)
        writer.add_vertex(v1)
        writer.add_vertex(v2)
        writer.add_edge(ApplicationEdge(v1, v_target), "Test")
        writer.add_edge(ApplicationEdge(v2, v_target), "Test")
        system_placements = Placements()
        system_placements.add_placement(Placement(v1.machine_vertex, 1, 0, 1))
        system_placements.add_placement(Placement(v2.machine_vertex, 0, 0, 2))
        self.make_infos(writer, system_placements)
        with self.assertRaises(KeyError):
            basic_routing_table_generator()

    def test_non_overlapping_different_chips(self) -> None:
        # Two vertices with non-overlapping routes can use the same key
        writer = PacmanDataWriter.mock()
        v_target_1 = FixedKeyAppVertex(None)
        v_target_2 = FixedKeyAppVertex(None)
        v1 = FixedKeyAppVertex(BaseKeyAndMask(0x1, 0xFFFFFFFF))
        v2 = FixedKeyAppVertex(BaseKeyAndMask(0x1, 0xFFFFFFFF))
        writer.add_vertex(v_target_1)
        writer.add_vertex(v_target_2)
        writer.add_vertex(v1)
        writer.add_vertex(v2)
        writer.add_edge(ApplicationEdge(v1, v_target_1), "Test")
        writer.add_edge(ApplicationEdge(v2, v_target_2), "Test")
        system_placements = Placements()
        system_placements.add_placement(Placement(v1.machine_vertex, 1, 0, 1))
        system_placements.add_placement(
            Placement(v_target_1.machine_vertex, 1, 0, 2))
        system_placements.add_placement(Placement(v2.machine_vertex, 0, 0, 2))
        system_placements.add_placement(
            Placement(v_target_2.machine_vertex, 0, 0, 3))
        self.make_infos(writer, system_placements)
        basic_routing_table_generator()
