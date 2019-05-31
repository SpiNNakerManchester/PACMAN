from six import itervalues
from spinn_utilities.progress_bar import ProgressBar
from spinn_machine import (
    Router, FixedRouteEntry, Machine, virtual_machine)
from pacman.model.graphs.machine import (
    MachineVertex, MachineGraph, MachineEdge)
from pacman.model.placements import Placements, Placement
from pacman.operations.router_algorithms import BasicDijkstraRouting
from pacman.exceptions import (
    PacmanAlreadyExistsException, PacmanConfigurationException)


class FixedRouteRouter(object):
    """ Fixed route router that makes a mirror path on every board based off\
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

        # lazy cheat
        fixed_route_tables = dict()

        if destination_class is None:
            return fixed_route_tables

        progress = ProgressBar(
            len(machine.ethernet_connected_chips),
            "generating fixed router routes.")

        # handle per board
        for ethernet_connected_chip in progress.over(
                machine.ethernet_connected_chips):
            ethernet_chip_x = ethernet_connected_chip.x
            ethernet_chip_y = ethernet_connected_chip.y

            # deduce which type of routing to do
            is_fully_working = self._detect_failed_chips_on_board(
                machine, ethernet_connected_chip, board_version)

            # if clean, use assumed routes
            if is_fully_working:
                self._do_fixed_routing(
                    fixed_route_tables, board_version, placements,
                    ethernet_chip_x, ethernet_chip_y, destination_class,
                    machine)
            else:  # use router for avoiding dead chips
                self._do_dynamic_routing(
                    fixed_route_tables, placements, ethernet_connected_chip,
                    destination_class, machine, board_version)
        return fixed_route_tables

    def _do_dynamic_routing(
            self, fixed_route_tables, placements, ethernet_connected_chip,
            destination_class, machine, board_version):
        """ Uses a router to route fixed routes

        :param fixed_route_tables: fixed route tables entry holder
        :param placements: placements
        :param ethernet_connected_chip: the chip to consider for this routing
        :param destination_class: the class at the Ethernet connected chip\
            for receiving all these routes.
        :param machine: SpiNNMachine instance
        :param board_version: The version of the machine
        :rtype: None
        """
        graph = MachineGraph(label="routing graph")
        fake_placements = Placements()

        # build fake setup for the routing
        eth_x = ethernet_connected_chip.x
        eth_y = ethernet_connected_chip.y
        down_links = set()
        for (chip_x, chip_y) in machine.get_existing_xys_on_board(
                ethernet_connected_chip):
            vertex = RoutingMachineVertex()
            graph.add_vertex(vertex)
            rel_x = chip_x - eth_x
            if rel_x < 0:
                rel_x += machine.max_chip_x + 1
            rel_y = chip_y - eth_y
            if rel_y < 0:
                rel_y += machine.max_chip_y + 1

            free_processor = 0
            while ((free_processor < machine.MAX_CORES_PER_CHIP) and
                   fake_placements.is_processor_occupied(
                       self.FAKE_ETHERNET_CHIP_X,
                       y=self.FAKE_ETHERNET_CHIP_Y,
                       p=free_processor)):
                free_processor += 1

            fake_placements.add_placement(Placement(
                x=rel_x, y=rel_y, p=free_processor, vertex=vertex))
            down_links.update({
                (rel_x, rel_y, link) for link in range(
                    Router.MAX_LINKS_PER_ROUTER)
                if not machine.is_link_at(chip_x, chip_y, link)})

        # Create a fake machine consisting of only the one board that
        # the routes should go over
        fake_machine = machine
        if (board_version in machine.BOARD_VERSION_FOR_48_CHIPS and
                (machine.max_chip_x > machine.MAX_CHIP_X_ID_ON_ONE_BOARD or
                 machine.max_chip_y > machine.MAX_CHIP_Y_ID_ON_ONE_BOARD)):
            down_chips = {
                (x, y) for x, y in zip(
                    range(machine.SIZE_X_OF_ONE_BOARD),
                    range(machine.SIZE_Y_OF_ONE_BOARD))
                if not machine.is_chip_at(
                    (x + eth_x) % (machine.max_chip_x + 1),
                    (y + eth_y) % (machine.max_chip_y + 1))}

            # build a fake machine which is just one board but with the missing
            # bits of the real board
            fake_machine = virtual_machine(
                machine.SIZE_X_OF_ONE_BOARD, machine.SIZE_Y_OF_ONE_BOARD,
                False, down_chips=down_chips, down_links=down_links,
                validate=False)

        # build destination
        verts = graph.vertices
        vertex_dest = RoutingMachineVertex()
        graph.add_vertex(vertex_dest)
        destination_processor = self._locate_destination(
            ethernet_chip_x=ethernet_connected_chip.x,
            ethernet_chip_y=ethernet_connected_chip.y,
            destination_class=destination_class,
            placements=placements)
        fake_placements.add_placement(Placement(
            x=self.FAKE_ETHERNET_CHIP_X, y=self.FAKE_ETHERNET_CHIP_Y,
            p=destination_processor, vertex=vertex_dest))

        # deal with edges
        for vertex in verts:
            graph.add_edge(
                MachineEdge(pre_vertex=vertex, post_vertex=vertex_dest),
                self.FAKE_ROUTING_PARTITION)

        # route as if using multicast
        router = BasicDijkstraRouting()
        routing_tables_by_partition = router(
            placements=fake_placements, machine=fake_machine,
            machine_graph=graph, use_progress_bar=False)

        # convert to fixed route entries
        for (chip_x, chip_y) in routing_tables_by_partition.get_routers():
            mc_entries = routing_tables_by_partition.get_entries_for_router(
                chip_x, chip_y)
            # only want the first entry, as that will all be the same.
            mc_entry = next(itervalues(mc_entries))
            fixed_route_entry = FixedRouteEntry(
                link_ids=mc_entry.link_ids,
                processor_ids=mc_entry.processor_ids)
            x = (chip_x + eth_x) % (machine.max_chip_x + 1)
            y = (chip_y + eth_y) % (machine.max_chip_y + 1)
            key = (x, y)
            if key in fixed_route_tables:
                raise PacmanAlreadyExistsException(
                    "fixed route entry", str(key))
            fixed_route_tables[key] = fixed_route_entry

    def _do_fixed_routing(
            self, fixed_route_tables, board_version, placements,
            ethernet_chip_x, ethernet_chip_y, destination_class, machine):
        """ Handles this board through the quick routing process, based on a\
            predefined routing table.

        :param fixed_route_tables: fixed routing tables
        :param board_version: the SpiNNaker machine version
        :param placements: the placements object
        :param ethernet_chip_x: chip x of the Ethernet connected chip
        :param ethernet_chip_y: chip y of the Ethernet connected chip
        :param destination_class: \
            the class of the vertex to route to at the Ethernet connected chip
        :param machine: SpiNNMachine instance
        :rtype: None
        """

        joins, paths = self._get_joins_paths(board_version)

        for path_id in paths:
            # create entry for each chip along path
            for (path_chip_x, path_chip_y) in paths[path_id]:
                # figure link IDs (default is [4])
                link_ids = [self.DEFAULT_LINK_ID]
                if (path_chip_x, path_chip_y) in joins:
                    link_ids = [joins[path_chip_x, path_chip_y]]

                # build entry and add to table and add to tables
                fixed_route_entry = FixedRouteEntry(
                    link_ids=link_ids, processor_ids=[])
                chip_x = (
                    path_chip_x + ethernet_chip_x) % (machine.max_chip_x + 1)
                chip_y = (
                    path_chip_y + ethernet_chip_y) % (machine.max_chip_y + 1)
                fixed_route_tables[chip_x, chip_y] = fixed_route_entry

        # locate where to put data
        processor_id = self._locate_destination(
            ethernet_chip_x, ethernet_chip_y, destination_class, placements)

        # create final fixed route entry
        # build entry and add to table and add to tables
        fixed_route_entry = FixedRouteEntry(
            link_ids=[], processor_ids=[processor_id])
        key = (ethernet_chip_x, ethernet_chip_y)
        if key in fixed_route_tables:
            raise PacmanAlreadyExistsException(
                "fixed route entry", str(key))
        fixed_route_tables[key] = fixed_route_entry

    def _get_joins_paths(self, board_version):
        # process each path separately
        if board_version in Machine.BOARD_VERSION_FOR_48_CHIPS:
            return self.joins_48, self.router_path_chips_48
        return self.joins_4, self.router_path_chips_4

    @staticmethod
    def _locate_destination(
            ethernet_chip_x, ethernet_chip_y, destination_class, placements):
        """ Locate destination vertex on Ethernet connected chip to send\
            fixed data to

        :param ethernet_chip_x: chip x to search
        :param ethernet_chip_y: chip y to search
        :param destination_class: the class of vertex to search for
        :param placements: the placements objects
        :return: processor ID as a int, or None if no valid processor found
        :rtype: int or None
        """
        for processor_id in range(0, Machine.MAX_CORES_PER_CHIP):
            # only check occupied processors
            if placements.is_processor_occupied(
                    ethernet_chip_x, ethernet_chip_y, processor_id):
                # verify if vertex correct one
                if isinstance(
                        placements.get_vertex_on_processor(
                            ethernet_chip_x, ethernet_chip_y, processor_id),
                        destination_class):
                    return processor_id
        raise PacmanConfigurationException(
            "no destination vertex found on Ethernet chip {}:{}".format(
                ethernet_chip_x, ethernet_chip_y))

    def _detect_failed_chips_on_board(
            self, machine, ethernet_connected_chip, board_version):
        """ Detects if all chips on the board are alive.

        :param machine: the SpiNNMachine instance
        :param ethernet_connected_chip: \
            the chip which supports an Ethernet connection
        :param board_version: what type of SpiNNaker board we're working with
        :return: True exactly when the machine is fully working
        :rtype: bool
        """
        # Check for correct chips by counting them
        num_working_chips = len(list(
            machine.get_existing_xys_on_board(ethernet_connected_chip)))
        if (board_version in Machine.BOARD_VERSION_FOR_4_CHIPS
                and num_working_chips != Machine.MAX_CHIPS_PER_4_CHIP_BOARD):
            return False
        if (board_version in Machine.BOARD_VERSION_FOR_48_CHIPS
                and num_working_chips != Machine.MAX_CHIPS_PER_48_BOARD):
            return False

        # figure correct links
        joins, _ = self._get_joins_paths(board_version)
        for ethernet_chip in machine.ethernet_connected_chips:
            ethernet_chip_x = ethernet_chip.x
            ethernet_chip_y = ethernet_chip.y
            for chip_x, chip_y in machine.get_existing_xys_on_board(ethernet_chip):
                join_chip_x = chip_x - ethernet_chip_x
                join_chip_y = chip_y - ethernet_chip_y
                if (join_chip_x, join_chip_y) in joins:
                    if not machine.is_link_at(
                            chip_x, chip_y, joins[join_chip_x, join_chip_y]):
                        return False
                elif (
                        join_chip_x != self.FAKE_ETHERNET_CHIP_X or
                        join_chip_y != self.FAKE_ETHERNET_CHIP_Y):
                    if not machine.is_link_at(
                            chip_x, chip_y, self.DEFAULT_LINK_ID):
                        return False
        return True


class RoutingMachineVertex(MachineVertex):
    @property
    def resources_required(self):
        return None
