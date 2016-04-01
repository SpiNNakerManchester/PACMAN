
from pacman.model.routing_tables.multicast_routing_table import \
    MulticastRoutingTable
from pacman.model.routing_tables.multicast_routing_tables import \
    MulticastRoutingTables

from spinn_machine.multicast_routing_entry import MulticastRoutingEntry
from spinn_machine.utilities.progress_bar import ProgressBar

MAX_KEYS_SUPPORTED = 2048
MASK = 0xFFFFF800


class BasicRoutingTableGenerator(object):
    """ An basic algorithm that can produce routing tables
    """

    def __call__(
            self, routing_infos, routing_table_by_partitions,
            machine):
        """

        :param routing_infos:
        :param routing_table_by_partitions:
        :param machine:
        :return:
        """
        progress_bar = ProgressBar(
            len(list(machine.chips)), "Generating routing tables")
        routing_tables = MulticastRoutingTables()
        for chip in machine.chips:
            partitions_in_table = routing_table_by_partitions.\
                get_entries_for_router(chip.x, chip.y)
            if len(partitions_in_table) != 0:
                routing_table = MulticastRoutingTable(chip.x, chip.y)
                for partition in partitions_in_table:
                    keys_and_masks = routing_infos.\
                        get_keys_and_masks_from_partition(partition)
                    entry = partitions_in_table[partition]
                    for key_and_mask in keys_and_masks:
                        multicast_routing_entry = MulticastRoutingEntry(
                            routing_entry_key=key_and_mask.key_combo,
                            defaultable=entry.defaultable,
                            mask=key_and_mask.mask,
                            link_ids=entry.out_going_links,
                            processor_ids=entry.out_going_processors)
                        routing_table.add_mutlicast_routing_entry(
                            multicast_routing_entry)
                routing_tables.add_routing_table(routing_table)
            progress_bar.update()
        progress_bar.end()

        return {"router_tables": routing_tables}
