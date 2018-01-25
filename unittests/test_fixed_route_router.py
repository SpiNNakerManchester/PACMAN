from spinn_machine import VirtualMachine
from pacman.model.placements import Placements, Placement
import pytest
from pacman.operations.fixed_route_router.fixed_route_router \
    import FixedRouteRouter


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
    "width,height,with_wrap_arounds,version,board_version",
    [(2, 2, True, None, 3),
     (2, 2, False, None, 3),
     (None, None, None, 3, 3),
     (8, 8, None, None, 5),
     (None, None, None, 5, 5),
     (12, 12, True, None, 5),
     (16, 16, False, None, 5)])
@pytest.mark.parametrize(
    "with_down_links,with_down_chips",
    [(False, False),
     (True, False),
     (False, True)])
def test_all_working(
        width, height, with_wrap_arounds, version, board_version,
        with_down_links, with_down_chips):

    router = FixedRouteRouter()

    joins, _ = router._get_joins_paths(board_version)
    temp_machine = VirtualMachine(
        width=width, height=height, with_wrap_arounds=with_wrap_arounds,
        version=version)
    down_links = None
    if with_down_links:
        down_links = set()
        for ethernet_chip in temp_machine.ethernet_connected_chips:
            down_links.add((ethernet_chip.x + 1, ethernet_chip.y, joins[1, 0]))
            down_links.add((ethernet_chip.x, ethernet_chip.y + 1, joins[0, 1]))
    down_chips = None
    if with_down_chips:
        down_chips = set()
        for ethernet_chip in temp_machine.ethernet_connected_chips:
            down_chips.add((ethernet_chip.x + 1, ethernet_chip.y + 1))
    machine = VirtualMachine(
        width=width, height=height, with_wrap_arounds=with_wrap_arounds,
        version=version, down_links=down_links, down_chips=down_chips)

    placements = Placements()

    ethernet_chips = machine.ethernet_connected_chips
    for ethernet_chip in ethernet_chips:
        destination_vertex = DestinationVertex()
        placements.add_placement(Placement(
            destination_vertex, ethernet_chip.x, ethernet_chip.y, 1))

    for ethernet_chip in ethernet_chips:
        uses_simple_routes = router._detect_failed_chips_on_board(
            machine, ethernet_chip, board_version)
        assert((with_down_chips or with_down_links) != uses_simple_routes)

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


if __name__ == '__main__':
    iterations = [
        (False, False),
        (True, False),
        (False, True)]
    for (x, y) in iterations:
        test_all_working(2, 2, True, None, 3, x, y)
        test_all_working(2, 2, False, None, 3, x, y)
        test_all_working(None, None, None, 3, 3, x, y)
        test_all_working(8, 8, None, None, 5, x, y)
        test_all_working(None, None, None, 5, 5, x, y)
        test_all_working(12, 12, True, None, 5, x, y)
        test_all_working(16, 16, False, None, 5, x, y)
