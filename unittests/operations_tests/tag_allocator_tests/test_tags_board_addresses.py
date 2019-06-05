from __future__ import absolute_import, print_function
import unittest
try:
    from collections.abc import defaultdict
except ImportError:
    from collections import defaultdict
from spinn_machine import virtual_machine
from pacman.model.placements import Placement, Placements
from pacman.model.graphs.machine import SimpleMachineVertex
from pacman.model.resources import ResourceContainer, IPtagResource
from pacman.operations.tag_allocator_algorithms import BasicTagAllocator


class TestTagsBoardAddresses(unittest.TestCase):
    """ Tests for ip tags on different boards
    """

    def test_ip_tags(self):
        machine = virtual_machine(12, 12)
        eth_chips = machine.ethernet_connected_chips
        vertices = [
            SimpleMachineVertex(
                ResourceContainer(iptags=[IPtagResource(
                    "127.0.0.1", port=None, strip_sdp=True)]),
                label="Vertex {}".format(i))
            for i in range(len(eth_chips))]
        print("Created {} vertices".format(len(vertices)))
        placements = Placements(
            Placement(vertex, chip.x, chip.y, 1)
            for vertex, chip in zip(vertices, eth_chips))
        allocator = BasicTagAllocator()
        _, _, tags = allocator(
            machine, plan_n_timesteps=None, placements=placements)

        for vertex, chip in zip(vertices, eth_chips):
            iptags = tags.get_ip_tags_for_vertex(vertex)
            self.assertEquals(
                len(iptags), 1, "Incorrect number of tags assigned")
            self.assertEquals(
                iptags[0].destination_x, chip.x,
                "Destination of tag incorrect")
            self.assertEquals(
                iptags[0].destination_y, chip.y,
                "Destination of tag incorrect")
            placement = placements.get_placement_of_vertex(vertex)
            print(placement, "has tag", iptags[0])

    def test_too_many_ip_tags_for_1_board(self):
        n_extra_vertices = 3
        machine = virtual_machine(12, 12)
        eth_chips = machine.ethernet_connected_chips
        eth_chip = eth_chips[0]
        eth_chip_2 = machine.get_chip_at(eth_chip.x + 1, eth_chip.y + 1)
        eth_procs = [
            proc.processor_id for proc in eth_chip.processors
            if not proc.is_monitor]
        procs = [proc for proc in eth_chip_2.processors if not proc.is_monitor]
        eth2_procs = [proc.processor_id for proc in procs]
        proc = procs[-1]
        eth_vertices = [
            SimpleMachineVertex(
                ResourceContainer(iptags=[IPtagResource(
                    "127.0.0.1", port=tag, strip_sdp=True)]),
                label="Ethernet Vertex {}".format(proc))
            for tag in eth_chip.tag_ids]
        eth2_vertices = [
            SimpleMachineVertex(
                ResourceContainer(iptags=[IPtagResource(
                    "127.0.0.1", port=10000 + tag, strip_sdp=True)]),
                label="Ethernet 2 Vertex {}".format(proc))
            for tag in range(n_extra_vertices)]
        placements = Placements(
            Placement(vertex, eth_chip.x, eth_chip.y, proc)
            for proc, vertex in zip(eth_procs, eth_vertices))
        placements.add_placements(
            Placement(vertex, eth_chip_2.x, eth_chip_2.y, proc)
            for proc, vertex in zip(eth2_procs, eth2_vertices))
        allocator = BasicTagAllocator()
        _, _, tags = allocator(
            machine, plan_n_timesteps=None, placements=placements)

        tags_by_board = defaultdict(set)
        for vertices in (eth_vertices, eth2_vertices):
            for vertex in vertices:
                iptags = tags.get_ip_tags_for_vertex(vertex)
                self.assertEquals(
                    len(iptags), 1, "Incorrect number of tags assigned")
                placement = placements.get_placement_of_vertex(vertex)
                print(placement, "has tag", iptags[0])
                self.assertFalse(
                    iptags[0].tag in tags_by_board[iptags[0].board_address],
                    "Tag used more than once")
                tags_by_board[iptags[0].board_address].add(iptags[0].tag)

        self.assertEquals(
            len(tags_by_board[eth_chip.ip_address]), len(eth_chip.tag_ids),
            "Wrong number of tags assigned to first Ethernet")
