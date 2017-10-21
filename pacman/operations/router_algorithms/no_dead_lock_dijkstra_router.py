
# pacman imports
from pacman.operations.router_algorithms import BasicDijkstraRouting

# spinnMachine imports
from spinn_machine.chip import Chip
from spinn_machine.link import Link
from spinn_machine.machine import Machine
from spinn_machine.router import Router


class NoDeadLockDijkstraRouter(BasicDijkstraRouting):

    def __init__(self):
        BasicDijkstraRouting.__init__(self)

    def __call__(
            self, placements, machine, partitioned_graph, k=1, l=0, m=0,
            bw_per_route_entry=BasicDijkstraRouting.BW_PER_ROUTE_ENTRY,
            max_bw=BasicDijkstraRouting.MAX_BW):
        """

        :param placements:
        :param machine:
        :param partitioned_graph:
        :param k:
        :param l:
        :param m:
        :param bw_per_route_entry:
        :param max_bw:
        :return:
        """

        has_wrap_arounds = self._detect_wrap_arounds(machine)
        if has_wrap_arounds:
            new_machine = \
                self._convert_machine_to_up_and_across_routing(machine)
        else:
            new_machine = \
                self._convert_machine_to_circual_routing(machine)

        return BasicDijkstraRouting.__call__(
            self, placements, new_machine, partitioned_graph, k, l, m,
            bw_per_route_entry, max_bw)

    @staticmethod
    def _detect_wrap_arounds(new_machine):

        # get first chip
        first_chip = list(new_machine.chips)[0]

        # keep iterating till either no link, or land back at first chip
        current_chip = first_chip
        found_loop = False
        while True:
            link_destination_x = current_chip.router.get_link(0).destination_x
            link_destination_y = current_chip.router.get_link(0).destination_y
            if new_machine.is_chip_at(link_destination_x, link_destination_y):
                current_chip = new_machine.get_chip_at(
                    link_destination_x, link_destination_y)
                if current_chip == first_chip:
                    found_loop = True
                    break
            else:
                break

        return found_loop

    @staticmethod
    def _convert_machine_to_up_and_across_routing(machine):
        new_machine = Machine([])
        for chip in machine.chips:
            router = chip.router

            # locate correct links to keep
            links_to_keep = list()
            for link in router.links:
                if 2 >= link.source_link_id >= 0:
                    links_to_keep.append(link)

            # build list of new links
            new_links = list()
            for link in links_to_keep:
                new_links.append(Link(
                    source_x=link.source_x, source_y=link.source_y,
                    source_link_id=link.source_link_id,
                    destination_x=link.destination_x,
                    destination_y=link.destination_y,
                    multicast_default_from=link.multicast_default_from,
                    multicast_default_to=link.multicast_default_to))

            # build new router
            new_router = Router(
                links=new_links,
                emergency_routing_enabled=router.emergency_routing_enabled,
                clock_speed=router.clock_speed,
                n_available_multicast_entries=(
                    router.n_available_multicast_entries))

            # build new chip
            new_machine.add_chip(Chip(
                x=chip.x, y=chip.y, processors=chip.processors,
                router=new_router, sdram=chip.sdram,
                nearest_ethernet_x=chip.nearest_ethernet_x,
                nearest_ethernet_y=chip.nearest_ethernet_y,
                ip_address=chip.ip_address, virtual=chip.virtual,
                tag_ids=chip.tag_ids))
        return new_machine

    @staticmethod
    def _convert_machine_to_circual_routing(new_machine):
        return []
