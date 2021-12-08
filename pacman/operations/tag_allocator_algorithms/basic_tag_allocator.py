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

from collections import namedtuple, defaultdict
from spinn_utilities.progress_bar import ProgressBar
from spinn_utilities.ordered_set import OrderedSet
from spinn_machine.tags import IPTag, ReverseIPTag
from pacman.model.tags import Tags
from pacman.exceptions import PacmanNotFoundError

# An arbitrary range of ports from which to allocate ports to Reverse IP Tags
_BOARD_PORTS = range(17896, 18000)

# The set of tags available on any chip
_CHIP_TAGS = range(8)


_Task = namedtuple("_Task", "constraint, board, tag, vertex, placement")


def basic_tag_allocator(machine, placements):
    """
    Basic tag allocator that goes though the boards available and applies\
        the IP tags and reverse IP tags as needed.

    :param ~spinn_machine.Machine machine:
        The machine with respect to which to partition the application
        graph
    :param Placements placements:
    :return: list of IP Tags, list of Reverse IP Tags,
        tag allocation holder
    :rtype: tuple(list(~spinn_machine.tags.IPTag),
        list(~spinn_machine.tags.ReverseIPTag), Tags)
    """
    # Keep track of which tags are free by Ethernet chip
    tags_available = defaultdict(lambda: OrderedSet(_CHIP_TAGS))

    # Keep track of which ports are free by Ethernet chip
    ports_available = defaultdict(lambda: OrderedSet(_BOARD_PORTS))

    # Go through placements and find tags
    tags = Tags()
    progress = ProgressBar(placements.n_placements, "Allocating tags")
    for placement in progress.over(placements.placements):
        resources = placement.vertex.resources_required
        place_chip = machine.get_chip_at(placement.x, placement.y)
        eth_chip = machine.get_chip_at(place_chip.nearest_ethernet_x,
                                       place_chip.nearest_ethernet_y)
        tags_on_chip = tags_available[eth_chip.x, eth_chip.y]
        for iptag in resources.iptags:
            alloc_chip, tag = __get_chip_and_tag(
                iptag, eth_chip, tags_on_chip, machine, tags_available)
            tags.add_ip_tag(
                __create_tag(alloc_chip, placement, iptag, tag),
                placement.vertex)
        for reverse_iptag in resources.reverse_iptags:
            alloc_chip, tag = __get_chip_and_tag(
                reverse_iptag, eth_chip, tags_on_chip, machine, tags_available)
            port = __get_port(reverse_iptag, eth_chip, ports_available)
            tags.add_ip_tag(
                __create_reverse_tag(
                    eth_chip, placement, reverse_iptag, tag, port),
                placement.vertex)

    return tags


def __get_chip_and_tag(iptag, eth_chip, tags_on_chip, machine, tags_available):
    if iptag.tag is not None:
        tag = iptag.tag
        # Try the nearest Ethernet
        if iptag.tag in tags_on_chip:
            tags_on_chip.remove(iptag.tag)
            return eth_chip, tag
        else:
            return __find_tag_chip(machine, tags_available, tag), tag
    else:
        if tags_on_chip:
            tag = tags_on_chip.pop()
            return eth_chip, tag
        else:
            return __find_free_tag(machine, tags_available)


def __find_tag_chip(machine, tags_available, tag):
    for eth_chip in machine.ethernet_connected_chips:
        tags_on_chip = tags_available[eth_chip.x, eth_chip.y]
        if tag in tags_on_chip:
            tags_on_chip.remove(tag)
            return eth_chip
    raise PacmanNotFoundError(f"Tag {tag} not available on any Ethernet chip")


def __find_free_tag(machine, tags_available):
    for eth_chip in machine.ethernet_connected_chips:
        tags_on_chip = tags_available[eth_chip.x, eth_chip.y]
        if tags_on_chip:
            tag = tags_on_chip.pop()
            return eth_chip, tag
    raise PacmanNotFoundError(f"Out of tags!")


def __create_tag(eth_chip, placement, iptag, tag):
    return IPTag(
        eth_chip.ip_address, placement.x, placement.y,
        tag, iptag.ip_address, iptag.port,
        iptag.strip_sdp, iptag.traffic_identifier)


def __create_reverse_tag(eth_chip, placement, reverse_iptag, tag, port):
    return ReverseIPTag(
        eth_chip.ip_address, tag, port, placement.x, placement.y, placement.p,
        reverse_iptag.sdp_port)


def __get_port(reverse_ip_tag, eth_chip, ports_available):
    if reverse_ip_tag.port is not None:
        return reverse_ip_tag.port
    return ports_available[eth_chip.x, eth_chip.y].pop()
