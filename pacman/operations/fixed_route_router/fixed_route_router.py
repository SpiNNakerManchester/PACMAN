from spinn_machine.fixed_route_entry import FixedRouteEntry
from pacman import exceptions


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


    """

    # groups of chips which work to go down a specific link on the ethernet
    # connected chip
    router_path_chips = {
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

    # dict of source and destination to create fixed route router when not
    # default 4
    joins = {(0, 1): [5], (0, 2): [5], (0, 3): [5], (2, 1): [3], (1, 0): [3],
             (2, 0): [3], (3, 0): [3], (4, 0): [3], (5, 6): [5], (6, 6): [5]}

    def __call__(self, machine, placements, destination_class):
        """ runs the fixed route generator for all boards on machine

        :param machine: spinn machine object
        :param placements: placements object
        :param destination_class: the destination class to route packets to
        :return: router tables for fixed route paths
        """

        # lazy cheat
        fixed_route_tables = dict()

        # handle per board
        for ethernet_connected_chip in machine.ethernet_connected_chips:
            ethernet_chip_x = ethernet_connected_chip.x
            ethernet_chip_y = ethernet_connected_chip.y

            # process each path separately
            for path_id in self.router_path_chips.keys():

                # create entry for each chip along path
                for (path_chip_x, path_chip_y) in \
                        self.router_path_chips[path_id]:

                    # figure link ids (default is [4])
                    link_ids = [4]
                    if (path_chip_x, path_chip_y) in self.joins:
                        link_ids = self.joins[(path_chip_x, path_chip_y)]

                    # build entry and add to table and add to tables
                    fixed_route_entry = FixedRouteEntry(
                        link_ids=link_ids, processor_ids=[])
                    fixed_route_tables[(path_chip_x, path_chip_y)] = \
                        fixed_route_entry

            # locate destination vertex on ethernet connected chip  to send
            # fixed data to
            for processor_id in range(0, 18):

                # only check occupied processors
                if placements.is_processor_occupied(
                        ethernet_chip_x, ethernet_chip_y, processor_id):

                    # verify if vertex correct one
                    if isinstance(
                            placements.get_vertex_on_processor(
                                ethernet_chip_x, ethernet_chip_y,
                                processor_id), destination_class):

                        # build entry and add to table and add to tables
                        fixed_route_entry = FixedRouteEntry(
                            link_ids=[], processor_ids=[processor_id])
                        key = (ethernet_chip_x, ethernet_chip_y)
                        if key in fixed_route_tables:
                            raise exceptions.PacmanAlreadyExistsException(
                                "fixed route entry", str(key))
                        fixed_route_tables[key] = fixed_route_entry

        # hand back fixed route tables
        return fixed_route_tables
