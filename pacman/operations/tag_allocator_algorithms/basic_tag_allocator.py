# Copyright (c) 2015 The University of Manchester
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

from collections import defaultdict
from typing import Tuple, List, Dict, Union
from spinn_utilities.progress_bar import ProgressBar
from spinn_machine import Chip, Machine
from spinn_machine.tags import IPTag, ReverseIPTag
from pacman.data import PacmanDataView
from pacman.model.tags import Tags
from pacman.model.placements import Placement
from pacman.exceptions import PacmanNotFoundError
from pacman.model.resources.iptag_resource import IPtagResource
from pacman.model.resources.reverse_iptag_resource import ReverseIPtagResource

# An arbitrary range of ports from which to allocate ports to Reverse IP Tags
_BOARD_PORTS = range(17896, 18000)

# The set of tags available on any chip
_CHIP_TAGS = range(1, 8)


def basic_tag_allocator() -> Tags:
    """
    Basic tag allocator that goes though the boards available and applies
    the IP tags and reverse IP tags as needed.

    .. note::
        This does not actually allocate the tags, but just produces the plan
        of what to allocate. Allocations need access to the running machine.

    :return: tag allocation holder
    """
    # Keep track of which tags are free by Ethernet chip
    tags_available: Dict[Chip, List[int]] = defaultdict(
        lambda: list(_CHIP_TAGS))

    # Keep track of which ports are free by Ethernet chip
    ports_available: Dict[Chip, List[int]] = defaultdict(
        lambda: list(_BOARD_PORTS))

    # Go through placements and find tags
    tags = Tags()

    progress = ProgressBar(
        PacmanDataView.get_n_placements(), "Allocating tags")
    machine = PacmanDataView.get_machine()
    for placement in progress.over(PacmanDataView.iterate_placemements()):
        place_chip = machine[placement.x, placement.y]
        eth_chip = machine[place_chip.nearest_ethernet_x,
                           place_chip.nearest_ethernet_y]
        for iptag in placement.vertex.iptags:
            alloc_chip, tag = __get_chip_and_tag(
                iptag, eth_chip, machine, tags_available)
            tags.add_ip_tag(
                __create_tag(alloc_chip, placement, iptag, tag),
                placement.vertex)
        for reverse_iptag in placement.vertex.reverse_iptags:
            alloc_chip, tag = __get_chip_and_tag(
                reverse_iptag, eth_chip, machine, tags_available)
            port = __get_port(reverse_iptag, eth_chip, ports_available)
            tags.add_reverse_ip_tag(
                __create_reverse_tag(
                    eth_chip, placement, reverse_iptag, tag, port),
                placement.vertex)

    return tags


def __get_chip_and_tag(
        iptag: Union[IPtagResource, ReverseIPtagResource], eth_chip: Chip,
        machine: Machine, tags_available: Dict[Chip, List[int]]
        ) -> Tuple[Chip, int]:
    tags_on_chip = tags_available[eth_chip]
    tag = iptag.tag
    if tag is not None:
        # Try the nearest Ethernet
        if tag in tags_on_chip:
            tags_on_chip.remove(tag)
            return eth_chip, tag
        return __find_tag_chip(machine, tags_available, tag), tag
    else:
        if tags_on_chip:
            # pop from back so automatic allocation starts with highest
            return eth_chip, tags_on_chip.pop()
        return __find_free_tag(machine, tags_available)


def __find_tag_chip(machine: Machine, tags_available: Dict[Chip, List[int]],
                    tag: int) -> Chip:
    for eth_chip in machine.ethernet_connected_chips:
        tags_on_chip = tags_available[eth_chip]
        if tag in tags_on_chip:
            tags_on_chip.remove(tag)
            return eth_chip
    raise PacmanNotFoundError(f"Tag {tag} not available on any Ethernet chip")


def __find_free_tag(
        machine: Machine,
        tags_available: Dict[Chip, List[int]]) -> Tuple[Chip, int]:
    for eth_chip in machine.ethernet_connected_chips:
        tags_on_chip = tags_available[eth_chip]
        if tags_on_chip:
            return eth_chip, tags_on_chip.pop(0)
    raise PacmanNotFoundError("Out of tags!")


def __create_tag(
        eth_chip: Chip, placement: Placement, iptag: IPtagResource,
        tag: int) -> IPTag:
    ethernet_ip = eth_chip.ip_address
    assert ethernet_ip is not None
    return IPTag(
        ethernet_ip, placement.x, placement.y,
        tag, iptag.ip_address, iptag.port,
        iptag.strip_sdp, iptag.traffic_identifier)


def __create_reverse_tag(
        eth_chip: Chip, placement: Placement,
        reverse_iptag: ReverseIPtagResource, tag: int,
        port: int) -> ReverseIPTag:
    ethernet_ip_address = eth_chip.ip_address
    assert ethernet_ip_address is not None
    return ReverseIPTag(
        ethernet_ip_address, tag, port, placement.x, placement.y, placement.p,
        reverse_iptag.sdp_port)


def __get_port(
        reverse_ip_tag: ReverseIPtagResource, eth_chip: Chip,
        ports_available: Dict[Chip, List[int]]) -> int:
    if reverse_ip_tag.port is not None:
        return reverse_ip_tag.port
    return ports_available[eth_chip].pop()
