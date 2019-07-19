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

import pytest
from spinn_machine import virtual_machine
from pacman.model.placements import Placements, Placement
from pacman.operations.fixed_route_router import FixedRouteRouter
# pylint: disable=protected-access


class DestinationVertex(object):
    pass


def _get_destinations(machine, fixed_route_tables, source_x, source_y):
    to_search = list([(source_x, source_y)])
    visited = set()
    destinations = set()
    while to_search:
        x, y = to_search.pop()
        assert (x, y) not in visited
        entry = fixed_route_tables[x, y]
        for link in entry.link_ids:
            assert machine.is_link_at(x, y, link)
            chip = machine.get_chip_at(x, y)
            link_obj = chip.router.get_link(link)
            to_search.append((link_obj.destination_x, link_obj.destination_y))
        for processor_id in entry.processor_ids:
            destinations.add((x, y, processor_id))
        visited.add((x, y))
    return destinations


@pytest.mark.parametrize(
    "width,height,version,board_version",
    [(2, 2, None, 3),
     (2, 2, None, 3),
     (None, None, 3, 3),
     (8, 8, None, 5),
     (None, None, 5, 5),
     (12, 12, None, 5),
     (16, 16, None, 5)])
@pytest.mark.parametrize(
    "with_down_links,with_down_chips",
    [(False, False),
     (True, False),
     (False, True)])
def test_all_working(
        width, height, version, board_version,
        with_down_links, with_down_chips):
    router = FixedRouteRouter()
    router._board_version = board_version

    joins, _ = router._get_joins_paths()
    temp_machine = virtual_machine(
        width=width, height=height, version=version)
    down_links = None
    if with_down_links:
        down_links = set()
        for ethernet_chip in temp_machine.ethernet_connected_chips:
            down_links.add((ethernet_chip.x + 1, ethernet_chip.y, joins[1, 0]))
            down_links.add((ethernet_chip.x, ethernet_chip.y + 1, joins[0, 1]))
    down_chips = None
    if with_down_chips:
        down_chips = set(
            (ethernet_chip.x + 1, ethernet_chip.y + 1)
            for ethernet_chip in temp_machine.ethernet_connected_chips)
    machine = virtual_machine(
        width=width, height=height, version=version,
        down_links=down_links, down_chips=down_chips)
    router._machine = machine

    ethernet_chips = machine.ethernet_connected_chips
    placements = Placements(
        Placement(DestinationVertex(), ethernet_chip.x, ethernet_chip.y, 1)
        for ethernet_chip in ethernet_chips)

    for ethernet_chip in ethernet_chips:
        uses_simple_routes = router._detect_failed_chips_on_board(
            ethernet_chip)
        assert((with_down_chips or with_down_links) != uses_simple_routes)

    fixed_route_tables = router(
        machine, placements, board_version, DestinationVertex)

    for x, y in machine.chip_coordinates:
        assert (x, y) in fixed_route_tables
        chip = machine.get_chip_at(x, y)
        destinations = _get_destinations(machine, fixed_route_tables, x, y)
        assert len(destinations) == 1
        assert (
            (chip.nearest_ethernet_x, chip.nearest_ethernet_y, 1)
            in destinations)


if __name__ == '__main__':
    iterations = [
        (False, False),
        (True, False),
        (False, True)]
    for (_x, _y) in iterations:
        test_all_working(2, 2, None, 3, _x, _y)
        test_all_working(2, 2,  None, 3, _x, _y)
        test_all_working(None, None, 3, 3, _x, _y)
        test_all_working(8, 8, None, 5, _x, _y)
        test_all_working(None, None, 5, 5, _x, _y)
        test_all_working(12, 12, None, 5, _x, _y)
        test_all_working(16, 16, None, 5, _x, _y)
