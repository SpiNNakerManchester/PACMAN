from spinn_machine import VirtualMachine
from pacman.model.placements import Placements, Placement
import pytest
from pacman.operations.fixed_route_router.fixed_route_router \
    import FixedRouteRouter


class DestinationVertex():
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
    "width,height,with_wrap_arounds,version,board_version",
    [(2, 2, True, None, 3),
     (2, 2, False, None, 3),
     (None, None, None, 3, 3),
     (8, 8, None, None, 5),
     (None, None, None, 5, 5),
     (12, 12, True, None, 5),
     (16, 16, False, None, 5)])
def test_all_working(width, height, with_wrap_arounds, version, board_version):
    machine = VirtualMachine(
        width=width, height=height, with_wrap_arounds=with_wrap_arounds,
        version=version)
    placements = Placements()

    ethernet_chips = machine.ethernet_connected_chips
    for ethernet_chip in ethernet_chips:
        destination_vertex = DestinationVertex()
        placements.add_placement(Placement(
            destination_vertex, ethernet_chip.x, ethernet_chip.y, 1))

    router = FixedRouteRouter()

    for ethernet_chip in ethernet_chips:
        assert(router._detect_failed_chips_on_board(
            machine, ethernet_chip, board_version))

    fixed_route_tables = router.__call__(
        machine, placements, board_version, DestinationVertex)

    for x, y in machine.chip_coordinates:
        assert (x, y) in fixed_route_tables
        chip = machine.get_chip_at(x, y)
        destinations = _get_destinations(machine, fixed_route_tables, x, y)
        assert len(destinations) == 1
        assert (
            (chip.nearest_ethernet_x, chip.nearest_ethernet_y, 1)
            in destinations)


@pytest.mark.parametrize(
    "width,height,with_wrap_arounds,version,board_version,down_links",
    [(2, 2, True, None, 3),
     (2, 2, False, None, 3),
     (None, None, None, 3, 3),
     (8, 8, None, None, 5),
     (None, None, None, 5, 5),
     (12, 12, True, None, 5),
     (16, 16, False, None, 5)])
def test_missing_links(
        width, height, with_wrap_arounds, version, board_version, down_links):
    machine = VirtualMachine(
        width=width, height=height, with_wrap_arounds=with_wrap_arounds,
        version=version, down_links=down_links)
    placements = Placements()

    ethernet_chips = machine.ethernet_connected_chips
    for ethernet_chip in ethernet_chips:
        destination_vertex = DestinationVertex()
        placements.add_placement(Placement(
            destination_vertex, ethernet_chip.x, ethernet_chip.y, 1))

    router = FixedRouteRouter()

    for ethernet_chip in ethernet_chips:
        assert(not router._detect_failed_chips_on_board(
            machine, ethernet_chip, board_version))

    fixed_route_tables = router.__call__(
        machine, placements, board_version, DestinationVertex)

    for x, y in machine.chip_coordinates:
        assert (x, y) in fixed_route_tables
        chip = machine.get_chip_at(x, y)
        destinations = _get_destinations(machine, fixed_route_tables, x, y)
        assert len(destinations) == 1
        assert (
            (chip.nearest_ethernet_x, chip.nearest_ethernet_y, 1)
            in destinations)
