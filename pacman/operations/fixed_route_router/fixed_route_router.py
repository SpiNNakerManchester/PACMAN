from pacman.model.graphs.machine import MachineVertex, MachineGraph, \
    MachineEdge
from pacman.model.placements import Placements, Placement
from pacman.operations.router_algorithms import BasicDijkstraRouting
from spinn_machine.fixed_route_entry import FixedRouteEntry
from pacman import exceptions
from spinn_utilities.progress_bar import ProgressBar


class FixedRouteRouter(object):
    """ fixed router that makes a mirror path on every board based off the
    below diagram. It assumed there's a core on the ethernet connected chip
    that is of the destination class.


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

    or

    [] []
    | /
    []-[]

    or router based to avoid dead chips

    """

    # groups of chips which work to go down a specific link on the ethernet
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
    joins_48 = {(0, 1): [5], (0, 2): [5], (0, 3): [5], (2, 1): [3],
                (1, 0): [3], (2, 0): [3], (3, 0): [3], (4, 0): [3],
                (5, 6): [5], (6, 6): [5]}
    joins_4 = {(0, 1): [5], (1, 0): [3]}

    FAKE_ROUTING_PARTITION = "FAKE_MC_ROUTE"

    def __call__(self, machine, placements, board_version, destination_class):
        """ runs the fixed route generator for all boards on machine

        :param machine: spinn machine object
        :param placements: placements object
        :param board_version: the version of spinnaker board using
        :param destination_class: the destination class to route packets to
        :return: router tables for fixed route paths
        """

        # lazy cheat
        fixed_route_tables = dict()

        progress_bar = ProgressBar(
            len(machine.ethernet_connected_chips),
            "generating fixed router routes.")

        if destination_class is None:
            progress_bar.end()
            return fixed_route_tables

        # handle per board
        for ethernet_connected_chip in progress_bar.over(
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
                    ethernet_chip_x, ethernet_chip_y, destination_class)
            else:  # use router for avoiding dead chips
                self._do_dynamic_routing(
                    fixed_route_tables, placements, ethernet_connected_chip,
                    destination_class, machine)
        return fixed_route_tables

    def _do_dynamic_routing(
            self, fixed_route_tables, placements, ethernet_connected_chip,
            destination_class, machine):
        """ uses a router to route fixed routes

        :param fixed_route_tables: fixed route tables entry holder
        :param placements: placements
        :param ethernet_connected_chip: the chip to consider for this routing
        :param destination_class: the class at the ethernet connected chip\
         for receiving all these routes.
        :param machine: SpiNNMachine instance
        :rtype: None
        """
        graph = MachineGraph(label="routing graph")
        fake_placements = Placements()

        # build fake setup for the routing
        for (chip_x, chip_y) in machine.get_chips_on_board(
                ethernet_connected_chip):
            vertex = RoutingMachineVertex()
            graph.add_vertex(vertex)
            fake_placements.add_placement(Placement(
                x=chip_x, y=chip_y, p=4, vertex=vertex))

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
            x=ethernet_connected_chip.x, y=ethernet_connected_chip.y,
            p=destination_processor, vertex=vertex_dest))

        # deal with edges
        for vertex in verts:
            graph.add_edge(
                MachineEdge(pre_vertex=vertex, post_vertex=vertex_dest),
                self.FAKE_ROUTING_PARTITION)

        # route as if using multicast
        router = BasicDijkstraRouting()
        routing_tables_by_partition = router(
            fake_placements, machine, graph)

        # convert to fr entries
        for (chip_x, chip_y) in machine.get_chips_on_board(
                ethernet_connected_chip):
            mc_entries = routing_tables_by_partition.get_entries_for_router(
                chip_x, chip_y)
            # only want the first entry, as that will all be the same.
            mc_entry = mc_entries[mc_entries.keys()[0]]
            fixed_route_entry = FixedRouteEntry(
                link_ids=mc_entry.out_going_links,
                processor_ids=mc_entry.out_going_processors)
            key = (chip_x, chip_y)
            if key in fixed_route_tables:
                raise exceptions.PacmanAlreadyExistsException(
                    "fixed route entry", str(key))
            fixed_route_tables[key] = fixed_route_entry

    def _do_fixed_routing(
            self, fixed_route_tables, board_version, placements,
            ethernet_chip_x, ethernet_chip_y, destination_class):
        """ handles this board through the quick routing process

        :param fixed_route_tables: fixed routing tables
        :param board_version: the spinnaker machine version
        :param placements: the placements object
        :param ethernet_chip_x: chip x of the ethernet connected chip
        :param ethernet_chip_y: chip y of the ethernet connected chip
        :param destination_class: the class of the vertex to route to at \
        the ethernet connected chip
        :rtype: None
        """

        # process each path separately
        if board_version == 3 or board_version == 4:
            paths = self.router_path_chips_48
            joins = self.joins_48
        else:
            paths = self.router_path_chips_4
            joins = self.joins_4

        for path_id in paths.keys():

            # create entry for each chip along path
            for (path_chip_x, path_chip_y) in paths[path_id]:

                # figure link ids (default is [4])
                link_ids = [4]
                if (path_chip_x, path_chip_y) in joins:
                    link_ids = joins[(path_chip_x, path_chip_y)]

                # build entry and add to table and add to tables
                fixed_route_entry = FixedRouteEntry(
                    link_ids=link_ids, processor_ids=[])
                fixed_route_tables[(path_chip_x, path_chip_y)] = \
                    fixed_route_entry

        # locate where to plonk data
        processor_id = self._locate_destination(
            ethernet_chip_x, ethernet_chip_y, destination_class, placements)

        # create final fixed route entry
        # build entry and add to table and add to tables
        fixed_route_entry = FixedRouteEntry(
            link_ids=[], processor_ids=[processor_id])
        key = (ethernet_chip_x, ethernet_chip_y)
        if key in fixed_route_tables:
            raise exceptions.PacmanAlreadyExistsException(
                "fixed route entry", str(key))
        fixed_route_tables[key] = fixed_route_entry

    @staticmethod
    def _locate_destination(
            ethernet_chip_x, ethernet_chip_y, destination_class, placements):
        """ locate destination vertex on ethernet connected chip to send\
        fixed data to

        :param ethernet_chip_x: chip x to search
        :param ethernet_chip_y: chip y to search
        :param destination_class: the class def to search for
        :param placements: the placements objects
        :return: processor id as a int or None if no valid processor found
        """
        for processor_id in range(0, 18):

            # only check occupied processors
            if placements.is_processor_occupied(
                    ethernet_chip_x, ethernet_chip_y, processor_id):

                # verify if vertex correct one
                if isinstance(
                        placements.get_vertex_on_processor(
                            ethernet_chip_x, ethernet_chip_y,
                            processor_id), destination_class):
                    return processor_id
        raise exceptions.PacmanConfigurationException(
            "no destination vertex found on ethernet chip {}:{}".format(
                ethernet_chip_x, ethernet_chip_y))

    @staticmethod
    def _detect_failed_chips_on_board(
            machine, ethernet_connected_chip, board_version):
        """ detects if all chips on the board are alive

        :param machine: the spiNNMachine instance
        :param ethernet_connected_chip: the chip which supports a ethernet\
         connection
        :param board_version: what type of SpiNNaker board we're working with
        :return: bool
        """
        return (
            ((board_version == 2 or board_version == 3) and
             len(list(machine.get_chips_on_board(
                 ethernet_connected_chip))) == 4)
            or ((board_version == 4 or board_version == 5) and
                len(list(machine.get_chips_on_board(
                    ethernet_connected_chip))) == 48))


class RoutingMachineVertex(MachineVertex):

    @property
    def resources_required(self):
        return None

    def __init__(self):
        MachineVertex.__init__(self)
