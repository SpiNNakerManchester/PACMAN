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

from six import itervalues
from spinn_utilities.progress_bar import ProgressBar
from spinn_machine import FixedRouteEntry, Machine, virtual_submachine
from pacman.model.graphs.machine import (
    MachineVertex, MachineGraph, MachineEdge)
from pacman.model.placements import Placements, Placement
from pacman.operations.router_algorithms import BasicDijkstraRouting
from pacman.exceptions import (
    PacmanAlreadyExistsException, PacmanConfigurationException)


class FixedRouteRouter(object):
    r""" Fixed route router that makes a mirror path on every board based off\
    the diagram below. It assumed there's a core on the Ethernet-connected\
    chip that is of the destination class. ::

                    [] [] [] []
                   /  /  /  /
                 [] [] [] [] []
                /  /   \  \ /
              [] [] [] [] [] []
             /  /  /  /  /  /
           [] [] [] [] [] [] []
          /  /  /  /  /  /  /
        [] [] [] [] [] [] [] []
        | /  /  /  /  /  /  /
        [] [] [] [] [] [] []
        | /  /  /  /  /  /
        [] []-[] [] [] []
        | /     /  /  /
        []-[]-[]-[]-[]

    or::

        [] []
        | /
        []-[]

    Falls back to classic algorithms when to avoid dead chips.
    """  # noqa: W605
    __slots__ = [
        "_board_version", "_destination_class", "_fixed_route_tables",
        "_machine", "_placements"]

    # groups of chips which work to go down a specific link on the Ethernet
    # connected chip
    router_path_chips_48 = {
        0: [
            (1, 0), (2, 0), (3, 0), (4, 0), (3, 1), (4, 1), (5, 1), (4, 2),
            (5, 2), (6, 2), (5, 3), (6, 3), (7, 3), (6, 4), (7, 4), (7, 5)],
        1: [
            (1, 1), (2, 1), (2, 2), (3, 2), (3, 3), (4, 3), (4, 4), (5, 4),
            (5, 5), (6, 5), (5, 6), (6, 6), (7, 6), (6, 7), (7, 7)],
        2: [
            (0, 1), (0, 2), (1, 2), (0, 3), (1, 3), (2, 3), (1, 4), (2, 4),
            (3, 4), (2, 5), (3, 5), (4, 5), (3, 6), (4, 6), (4, 7), (5, 7)
        ]}
    router_path_chips_4 = {0: [(1, 1), (0, 1), (1, 0)]}

    # dict of source and destination to create fixed route router when not
    # default 4 0 = E 1 = NE 2 = N 3 = W 4 = SW 5 = S
    joins_48 = {(0, 1): 5, (0, 2): 5, (0, 3): 5, (2, 1): 3,
                (1, 0): 3, (2, 0): 3, (3, 0): 3, (4, 0): 3,
                (5, 6): 5, (6, 6): 5}
    joins_4 = {(0, 1): 5, (1, 0): 3}

    FAKE_ETHERNET_CHIP_X = 0
    FAKE_ETHERNET_CHIP_Y = 0
    FAKE_ETHERNET_CHIP = (FAKE_ETHERNET_CHIP_X, FAKE_ETHERNET_CHIP_Y)
    FAKE_ROUTING_PARTITION = "FAKE_MC_ROUTE"
    DEFAULT_LINK_ID = 4

    def __call__(self, machine, placements, board_version, destination_class):
        """ Runs the fixed route generator for all boards on machine

        :param machine: SpiNNMachine object
        :param placements: placements object
        :param board_version: the version of SpiNNaker board being used
        :param destination_class: the destination class to route packets to
        :return: router tables for fixed route paths
        """
        # pylint: disable=attribute-defined-outside-init
        self._board_version = board_version
        self._machine = machine
        self._destination_class = destination_class
        self._placements = placements
        self._fixed_route_tables = dict()

        if destination_class is None:
            return self._fixed_route_tables

        progress = ProgressBar(
            len(machine.ethernet_connected_chips),
            "Generating fixed router routes")

        # handle per board
        for ethernet_chip in progress.over(machine.ethernet_connected_chips):
            # deduce which type of routing to do
            is_fully_working = self._detect_failed_chips_on_board(
                ethernet_chip)

            # if clean, use assumed routes
            if is_fully_working:
                self._do_fixed_routing(ethernet_chip)
            else:  # use router for avoiding dead chips
                self._do_dynamic_routing(ethernet_chip)
        return self._fixed_route_tables

    @staticmethod
    def __get_free_root_processor_id(machine, placements):
        for p in range(machine.MAX_CORES_PER_CHIP):
            if not placements.is_processor_occupied(0, 0, p):
                return p
        raise PacmanConfigurationException("no free processor found")

    def _do_dynamic_routing(self, ethernet_chip):
        """ Uses a router to route fixed routes

        :param ethernet_chip: the chip to consider for this routing
        :rtype: None
        """
        graph = MachineGraph(label="routing graph")
        fake_placements = Placements()

        # Create a fake machine consisting of only the one board that
        # the routes should go over
        fake_machine = virtual_submachine(self._machine, ethernet_chip)

        # build fake setup for the routing
        eth_x = ethernet_chip.x
        eth_y = ethernet_chip.y
        for chip in self._machine.get_chips_by_ethernet(eth_x, eth_y):
            vertex = RoutingMachineVertex()
            graph.add_vertex(vertex)

            free_processor = self.__get_free_root_processor_id(
                self._machine, fake_placements)
            rel_x, rel_y = self._machine.get_local_xy(chip)
            fake_placements.add_placement(Placement(
                x=rel_x, y=rel_y, p=free_processor, vertex=vertex))

        # build destination
        vertex_dest = RoutingMachineVertex()
        graph.add_vertex(vertex_dest)
        destination_processor = self.__locate_destination(eth_x, eth_y)
        fake_placements.add_placement(Placement(
            x=self.FAKE_ETHERNET_CHIP_X, y=self.FAKE_ETHERNET_CHIP_Y,
            p=destination_processor, vertex=vertex_dest))

        # deal with edges
        for vertex in graph.vertices:
            graph.add_edge(
                MachineEdge(pre_vertex=vertex, post_vertex=vertex_dest),
                self.FAKE_ROUTING_PARTITION)

        # route as if using multicast
        routing_tables_by_partition = self.__dijkstra_route(
            fake_machine, graph, fake_placements)

        # convert to fixed route entries
        for (chip_x, chip_y) in routing_tables_by_partition.get_routers():
            mc_entries = routing_tables_by_partition.get_entries_for_router(
                chip_x, chip_y)
            # only want the first entry, as that will all be the same.
            mc_entry = next(itervalues(mc_entries))
            self.__add_fixed_route_entry(
                self._machine.get_global_xy(chip_x, chip_y, eth_x, eth_y),
                mc_entry.link_ids, mc_entry.processor_ids)

    @staticmethod
    def __dijkstra_route(machine, graph, placements):
        router = BasicDijkstraRouting()
        return router(
            placements=placements, machine=machine, machine_graph=graph,
            use_progress_bar=False)

    def _do_fixed_routing(self, ethernet_connected_chip):
        """ Handles this board through the quick routing process, based on a\
            predefined routing table.

        :param ethernet_connected_chip: the Ethernet connected chip
        :rtype: None
        """

        joins, paths = self._get_joins_paths()
        eth_x = ethernet_connected_chip.x
        eth_y = ethernet_connected_chip.y

        for path_id in paths:
            # create entry for each chip along path
            for (path_chip_x, path_chip_y) in paths[path_id]:
                # figure link IDs (default is [4])
                link_ids = [self.DEFAULT_LINK_ID]
                if (path_chip_x, path_chip_y) in joins:
                    link_ids = [joins[path_chip_x, path_chip_y]]

                # build entry and add to table and add to tables
                self.__add_fixed_route_entry(
                    self._machine.get_global_xy(
                        path_chip_x, path_chip_y, eth_x, eth_y),
                    link_ids, [])

        # locate where to put data
        processor_id = self.__locate_destination(eth_x, eth_y)

        # create final fixed route entry
        # build entry and add to table and add to tables
        self.__add_fixed_route_entry((eth_x, eth_y), [], [processor_id])

    def __add_fixed_route_entry(self, key, link_ids, processor_ids):
        fixed_route_entry = FixedRouteEntry(
            link_ids=link_ids, processor_ids=processor_ids)
        if key in self._fixed_route_tables:
            raise PacmanAlreadyExistsException(
                "fixed route entry", str(key))
        self._fixed_route_tables[key] = fixed_route_entry

    # Non-private for testability
    def _get_joins_paths(self):
        # process each path separately
        if self._board_version in Machine.BOARD_VERSION_FOR_48_CHIPS:
            return self.joins_48, self.router_path_chips_48
        return self.joins_4, self.router_path_chips_4

    def __locate_destination(self, chip_x, chip_y):
        """ Locate destination vertex on Ethernet connected chip to send\
            fixed data to

        :param chip_x: chip x to search
        :param chip_y: chip y to search
        :return: processor ID as a int
        :rtype: int
        :raises PacmanConfigurationException: if no placement processor found
        """
        for processor_id in range(Machine.MAX_CORES_PER_CHIP):
            # only check occupied processors
            if self._placements.is_processor_occupied(
                    chip_x, chip_y, processor_id):
                # verify if vertex correct one
                if isinstance(
                        self._placements.get_vertex_on_processor(
                            chip_x, chip_y, processor_id),
                        self._destination_class):
                    return processor_id
        raise PacmanConfigurationException(
            "no destination vertex found on Ethernet chip {}:{}".format(
                chip_x, chip_y))

    def _detect_failed_chips_on_board(self, ethernet_chip):
        """ Detects if all chips on the board are alive.

        :param ethernet_chip: \
            the chip which supports an Ethernet connection
        :return: True exactly when the machine is fully working
        :rtype: bool
        """
        # Check for correct chips by counting them
        num_working_chips = sum(
            1 for _ in self._machine.get_existing_xys_on_board(
                ethernet_chip))
        if (self._board_version in Machine.BOARD_VERSION_FOR_4_CHIPS
                and num_working_chips != Machine.MAX_CHIPS_PER_4_CHIP_BOARD):
            return False
        if (self._board_version in Machine.BOARD_VERSION_FOR_48_CHIPS
                and num_working_chips != Machine.MAX_CHIPS_PER_48_BOARD):
            return False

        # figure correct links
        joins, _ = self._get_joins_paths()
        for ethernet_chip in self._machine.ethernet_connected_chips:
            for chip in self._machine.get_chips_by_ethernet(
                    ethernet_chip.x, ethernet_chip.y):
                join = self._machine.get_local_xy(chip)
                if join in joins:
                    if not chip.router.is_link(joins[join]):
                        return False
                elif join != self.FAKE_ETHERNET_CHIP:
                    if not chip.router.is_link(self.DEFAULT_LINK_ID):
                        return False
        return True


class RoutingMachineVertex(MachineVertex):
    @property
    def resources_required(self):
        return None
