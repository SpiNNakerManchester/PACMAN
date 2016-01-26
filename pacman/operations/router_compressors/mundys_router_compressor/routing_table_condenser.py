
# pacman imports
from pacman.model.routing_tables.multicast_routing_table import \
    MulticastRoutingTable
from pacman.model.routing_tables.multicast_routing_tables import \
    MulticastRoutingTables
from pacman import exceptions
from pacman.utilities.utility_objs.progress_bar import ProgressBar

# spinnMachine imports
from spinn_machine.multicast_routing_entry import MulticastRoutingEntry

# rig imports
from rig import routing_table as rig_routing_table
from rig.routing_table import ordered_covering as rigs_compressor

# general imports
import collections
import logging
import itertools

logger = logging.getLogger(__name__)


class MundyRouterCompressor(object):

    KeyMask = collections.namedtuple('KeyMask', 'key mask')
    RoutingEntry = collections.namedtuple('RoutingEntry',
                                          'key mask route defaultable')

    def __call__(self, router_tables, target_length=None):
        # build storage
        compressed_pacman_router_tables = MulticastRoutingTables()

        # create progress bar
        progress_bar = ProgressBar(
            len(router_tables.routing_tables), "Compressing routing Tables")

        # compress each router
        for router_table in router_tables.routing_tables:
            # convert to mundy format

            #print "start \n {}".format(router_table)

            entries = self._convert_to_mundy_format(router_table)

            #print "start after convert \n {}".format(entries)

            # compress the router entries
            compressed_router_table_entries = \
                rigs_compressor.minimise(entries, target_length)

            logger.info(
                "reduced router table {}:{} from {} entries to {} entries"
                .format(router_table.x, router_table.y, len(entries),
                        len(compressed_router_table_entries)))

            #print "compressed before conversion \n {}"\
            #    .format(compressed_router_table_entries)

            # convert back to pacman model
            compressed_pacman_table = self._convert_to_pacman_router_table(
                compressed_router_table_entries, router_table.x, router_table.y)

            #print "compressed after conversion \n{}"\
            #    .format(compressed_pacman_table)

            # add to new compressed routing tables
            compressed_pacman_router_tables.add_routing_table(
                compressed_pacman_table)

            progress_bar.update()
        progress_bar.end()

        # return
        return {'routing_tables': compressed_pacman_router_tables}

    def _convert_to_mundy_format(self, pacman_router_table):
        """

        :param pacman_router_table:
        :return:
        """
        entries = list()

        # handle entries
        for router_entry in pacman_router_table.multicast_routing_entries:
            # Get the route for the entry
            new_processor_ids = list()
            for processor_id in router_entry.processor_ids:
                new_processor_ids.append(processor_id + 6)


            route = set(rig_routing_table.Routes(i) for i in
                        itertools.chain(router_entry.link_ids,
                                        new_processor_ids))

            # Get the source for the entry
            if router_entry.defaultable:
                source = set([next(iter(route)).opposite])
            else:
                source = set([None])

            # Add the new entry
            entries.append(rig_routing_table.RoutingTableEntry(
                route, router_entry.routing_entry_key, router_entry.mask,
                source))

        return entries

    @staticmethod
    def _convert_to_pacman_router_table(
            mundy_compressed_router_table_entries, router_x_coord,
            router_y_coord):
        """

        :param mundy_compressed_router_table_entries:
        :param router_x_coord:
        :param router_y_coord:
        :return:
        """

        table = MulticastRoutingTable(router_x_coord, router_y_coord)
        for entry in mundy_compressed_router_table_entries:

            table.add_mutlicast_routing_entry(
                MulticastRoutingEntry(
                    entry.key, entry.mask,  # Key and mask
                    ((int(c) - 6) for c in entry.route if c.is_core),  # Cores
                    (int(l) for l in entry.route if l.is_link),  # Links
                    False))  # NOT defaultable
        return table
