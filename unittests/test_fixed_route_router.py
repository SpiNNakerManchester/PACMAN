# Copyright (c) 2017 The University of Manchester
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

import pytest
from typing import Dict, Set, Tuple

from spinn_utilities.config_holder import set_config

from spinn_machine import Machine, RoutingEntry, virtual_machine
from spinn_machine.version import FIVE

from pacman.config_setup import unittest_setup
from pacman.data.pacman_data_writer import PacmanDataWriter
from pacman.model.graphs.machine import SimpleMachineVertex
from pacman.model.placements import Placements, Placement
from pacman.operations.fixed_route_router import fixed_route_router
from pacman.exceptions import PacmanRoutingException


def _get_destinations(
        machine: Machine,
        fixed_route_tables: Dict[Tuple[int, int], RoutingEntry],
        source_x: int, source_y: int) -> Set[Tuple[int, int, int]]:
    to_search = list([(source_x, source_y)])
    visited = set()
    destinations: Set[Tuple[int, int, int]] = set()
    while to_search:
        x, y = to_search.pop()
        assert (x, y) not in visited
        entry = fixed_route_tables[x, y]
        for link in entry.link_ids:
            assert machine.is_link_at(x, y, link)
            chip = machine[x, y]
            link_obj = chip.router.get_link(link)
            assert link_obj is not None
            to_search.append((link_obj.destination_x, link_obj.destination_y))
        for processor_id in entry.processor_ids:
            destinations.add((x, y, processor_id))
        visited.add((x, y))
    return destinations


def _check_setup(width: int, height: int) -> None:
    machine = virtual_machine(width=width, height=height)
    writer = PacmanDataWriter.mock()
    writer.set_machine(machine)
    ethernet_chips = machine.ethernet_connected_chips
    writer.set_placements(
        Placements(Placement(
            SimpleMachineVertex(None), ethernet_chip.x, ethernet_chip.y, 1)
                   for ethernet_chip in ethernet_chips))

    fixed_route_tables = fixed_route_router(SimpleMachineVertex)

    for x, y in machine.chip_coordinates:
        assert (x, y) in fixed_route_tables
        chip = machine[x, y]
        destinations = _get_destinations(machine, fixed_route_tables, x, y)
        assert len(destinations) == 1
        assert (
            (chip.nearest_ethernet_x, chip.nearest_ethernet_y, 1)
            in destinations)


@pytest.mark.parametrize(
    "version, width,height",
    [(3, 2, 2),
     (5, 8, 8),
     (5, 12, 12),
     (5, 16, 16),
     (201, 1, 1)])
@pytest.mark.parametrize(
    "with_down_links,with_down_chips",
    [(False, False),
     (True, False),
     (False, True),
     (True, True)])
def test_all_working(width: int, height: int,  version: int,
                     with_down_links: bool, with_down_chips: bool) -> None:
    unittest_setup()
    set_config("Machine", "version", str(version))
    temp_machine = virtual_machine(width=width, height=height)
    down_links = None
    if with_down_links:
        down_links = set()
        for ethernet_chip in temp_machine.ethernet_connected_chips:
            down_links.add((ethernet_chip.x + 1, ethernet_chip.y, 5))
            down_links.add((ethernet_chip.x, ethernet_chip.y + 1, 3))
        down_str = ":".join([f"{x},{y},{link}" for x, y, link in down_links])
        set_config("Machine", "down_links", down_str)
    down_chips = None
    if with_down_chips:
        down_chips = set(
            (ethernet_chip.x + 1, ethernet_chip.y + 1)
            for ethernet_chip in temp_machine.ethernet_connected_chips)
        down_str = ":".join([f"{x},{y}" for x, y in down_chips])
        set_config("Machine", "down_chips", down_str)
    _check_setup(width, height)


def test_unreachable() -> None:
    unittest_setup()
    set_config("Machine", "version", str(FIVE))
    set_config("Machine", "down_chips", "0,2:1,3:1,4")
    with pytest.raises(PacmanRoutingException):
        _check_setup(8, 8)
