# Copyright (c) 2016 The University of Manchester
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
from collections import defaultdict
from typing import Dict, Set

from spinn_utilities.config_holder import set_config

from spinn_machine import Machine
from spinn_machine.version.version_strings import VersionStrings
from spinn_machine.virtual_machine import virtual_machine_by_boards

from pacman.config_setup import unittest_setup
from pacman.data import PacmanDataView
from pacman.data.pacman_data_writer import PacmanDataWriter
from pacman.exceptions import PacmanNotFoundError
from pacman.model.placements import Placement, Placements
from pacman.model.graphs.machine import SimpleMachineVertex
from pacman.model.resources import (
    ConstantSDRAM, IPtagResource, ReverseIPtagResource)
from pacman.operations.tag_allocator_algorithms import basic_tag_allocator


class TestTagsBoardAddresses(unittest.TestCase):
    """ Tests for ip tags on different boards
    """
    def setUp(self) -> None:
        unittest_setup()
        set_config("Machine", "versions", VersionStrings.BIG.text)

    def test_ip_tags(self) -> None:
        writer = PacmanDataWriter.mock()
        machine = virtual_machine_by_boards(3)
        writer.set_machine(machine)
        eth_chips = machine.ethernet_connected_chips
        vertices = [
            SimpleMachineVertex(
                sdram=ConstantSDRAM(0),
                iptags=[IPtagResource(
                    "127.0.0.1", port=123, strip_sdp=True)],
                label="Vertex {}".format(i))
            for i in range(len(eth_chips))]
        print("Created {} vertices".format(len(vertices)))
        placements = Placements(
            Placement(vertex, chip.x, chip.y, 1)
            for vertex, chip in zip(vertices, eth_chips))
        writer.set_placements(placements)
        writer.set_plan_n_timesteps(None)
        tags = basic_tag_allocator()

        for vertex, chip in zip(vertices, eth_chips):
            iptags = tags.get_ip_tags_for_vertex(vertex)
            assert iptags is not None
            self.assertEqual(
                len(iptags), 1, "Incorrect number of tags assigned")
            self.assertEqual(
                iptags[0].destination_x, chip.x,
                "Destination of tag incorrect")
            self.assertEqual(
                iptags[0].destination_y, chip.y,
                "Destination of tag incorrect")
            placement = placements.get_placement_of_vertex(vertex)
            print(placement, "has tag", iptags[0])

    def do_too_many_ip_tags_for_1_board(self, machine: Machine) -> None:
        writer = PacmanDataWriter.mock()
        n_extra_vertices = 3
        writer.set_machine(machine)
        eth_chips = machine.ethernet_connected_chips
        eth_chip = eth_chips[0]
        eth_chip_2 = machine[eth_chip.x + 1, eth_chip.y + 1]
        eth_procs = list(eth_chip.placable_processors_ids)
        eth2_procs = list(eth_chip_2.placable_processors_ids)
        proc = eth2_procs[-1]
        eth_vertices = [
            SimpleMachineVertex(
                sdram=ConstantSDRAM(0),
                iptags=[IPtagResource(
                    "127.0.0.1", port=tag, strip_sdp=True)],
                label="Ethernet Vertex {}".format(proc))
            for tag in eth_chip.tag_ids]
        eth2_vertices = [
            SimpleMachineVertex(
                sdram=ConstantSDRAM(0),
                iptags=[IPtagResource(
                    "127.0.0.1", port=10000 + tag, strip_sdp=True)],
                label="Ethernet 2 Vertex {}".format(proc))
            for tag in range(n_extra_vertices)]
        placements = Placements(
            Placement(vertex, eth_chip.x, eth_chip.y, proc)
            for proc, vertex in zip(eth_procs, eth_vertices))
        placements.add_placements(
            Placement(vertex, eth_chip_2.x, eth_chip_2.y, proc)
            for proc, vertex in zip(eth2_procs, eth2_vertices))
        writer.set_placements(placements)
        writer.set_plan_n_timesteps(1000)
        tags = basic_tag_allocator()

        tags_by_board: Dict[str, Set] = defaultdict(set)
        for vertices in (eth_vertices, eth2_vertices):
            for vertex in vertices:
                iptags = tags.get_ip_tags_for_vertex(vertex)
                assert iptags is not None
                self.assertEqual(
                    len(iptags), 1, "Incorrect number of tags assigned")
                placement = placements.get_placement_of_vertex(vertex)
                print(placement, "has tag", iptags[0])
                self.assertFalse(
                    iptags[0].tag in tags_by_board[iptags[0].board_address],
                    "Tag used more than once")
                tags_by_board[iptags[0].board_address].add(iptags[0].tag)

        ip_address = eth_chip.ip_address
        assert ip_address is not None
        self.assertEqual(
            len(tags_by_board[ip_address]), len(eth_chip.tag_ids),
            "Wrong number of tags assigned to first Ethernet")

    def test_fixed_tag(self) -> None:
        writer = PacmanDataWriter.mock()
        machine = writer.get_machine()
        chip00 = machine[0, 0]
        procs = chip00.placable_processors_ids
        placements = Placements()
        for i in range(5):
            vertex = SimpleMachineVertex(
                sdram=ConstantSDRAM(0),
                iptags=[IPtagResource(
                    "127.0.0.1", port=10000 + i, strip_sdp=True, tag=1+i)],
                label="Vertex {i}")
            placements.add_placement(Placement(vertex, 0, 0, procs[i]))
        writer.set_placements(placements)
        writer.set_plan_n_timesteps(1000)
        tags = basic_tag_allocator()
        self.assertEqual(5, len(list(tags.ip_tags)))
        self.assertEqual(5, len(list(tags.ip_tags_vertices)))

    def do_fixed_repeat_tag(self, machine: Machine) -> None:
        writer = PacmanDataWriter.mock()
        writer.set_machine(machine)
        chip00 = machine[0, 0]
        procs = chip00.placable_processors_ids
        placements = Placements()
        for i in range(3):
            vertex = SimpleMachineVertex(
                sdram=ConstantSDRAM(0),
                iptags=[IPtagResource("127.45.0.1", port=10000 + i,
                                      strip_sdp=True, tag=1 + i),
                        IPtagResource("127.45.0.1", port=10000 + i,
                                      strip_sdp=True, tag=1+i)],
                label=f"Vertex {i}")
            placements.add_placement(Placement(vertex, 0, 0, procs[i]))
        writer.set_placements(placements)
        writer.set_plan_n_timesteps(1000)
        tags = basic_tag_allocator()
        self.assertEqual(6, len(list(tags.ip_tags_vertices)))

    def test_too_many_ip_tags_for_1_board(self) -> None:
        machine = PacmanDataView.get_machine()
        with self.assertRaises(PacmanNotFoundError):
            self.do_too_many_ip_tags_for_1_board(machine)

    def test_spread_ip_tags(self) -> None:
        machine = virtual_machine_by_boards(3)
        self.do_too_many_ip_tags_for_1_board(machine)

    def test_fixed_repeat_tag_1_board(self) -> None:
        machine = PacmanDataView.get_machine()
        with self.assertRaises(PacmanNotFoundError):
            self.do_fixed_repeat_tag(machine)

    def test_fixed_repeat_tag_3_boards(self) -> None:
        machine = virtual_machine_by_boards(3)
        self.do_fixed_repeat_tag(machine)

    def do_reverse(self, machine: Machine) -> None:
        writer = PacmanDataWriter.mock()
        writer.set_machine(machine)
        chip00 = machine[0, 0]
        processor = chip00.placable_processors_ids[0]
        placements = Placements()
        vertex = SimpleMachineVertex(
            sdram=ConstantSDRAM(0),
            reverse_iptags=[ReverseIPtagResource(port=10000, tag=1)])
        placements.add_placement(Placement(vertex, 0, 0, processor))
        writer.set_placements(placements)
        writer.set_plan_n_timesteps(1000)
        tags = basic_tag_allocator()
        self.assertEqual(1, len(list(tags.reverse_ip_tags)))

    def test_do_reverse_3_boards(self) -> None:
        machine = virtual_machine_by_boards(3)
        self.do_reverse(machine)
