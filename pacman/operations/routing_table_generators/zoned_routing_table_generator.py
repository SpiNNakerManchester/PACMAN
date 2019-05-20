from spinn_utilities.progress_bar import ProgressBar
from spinn_utilities.ordered_default_dict import DefaultOrderedDict
from spinn_machine import MulticastRoutingEntry
from pacman.model.routing_tables import (
    MulticastRoutingTable, MulticastRoutingTables)


class ZonedRoutingTableGenerator(object):
    """ An basic algorithm that can produce routing tables
    """

    __slots__ = []

    def __call__(
            self, routing_infos, routing_table_by_partitions, machine, graph_mapper, info_by_app_vertex):
        """
        :param routing_infos:
        :param routing_table_by_partitions:
        :param machine:
        """
        progress = ProgressBar(machine.n_chips, "Generating routing tables")
        routing_tables = MulticastRoutingTables()
        for chip in progress.over(machine.chips):
            partitions_in_table = routing_table_by_partitions.\
                get_entries_for_router(chip.x, chip.y)
            if partitions_in_table:
                routing_tables.add_routing_table(self._create_routing_table(
                    chip, partitions_in_table, routing_infos, graph_mapper, info_by_app_vertex))

        return routing_tables

    def _create_routing_table(self, chip, partitions_in_table, routing_infos, graph_mapper, info_by_app_vertex):
        table = MulticastRoutingTable(chip.x, chip.y)
        partitions_by_app_vertex = DefaultOrderedDict(set)
        for partition in partitions_in_table:
            machine_vertex = partition.pre_vertex
            app_vertex = graph_mapper.get_application_vertex(machine_vertex)
            partitions_by_app_vertex[app_vertex].add(partition)
        for app_vertex in partitions_by_app_vertex:
            first_entry = None
            if app_vertex in info_by_app_vertex:
                mergable = True
                count = 0
                for partition in partitions_by_app_vertex[app_vertex]:
                    count += 1
                    entry = partitions_in_table[partition]
                    if first_entry is None:
                        first_entry = entry
                    else:
                        if first_entry.link_ids != entry.link_ids:
                            mergable = False
                            break
                        if first_entry.processor_ids != entry.processor_ids:
                            mergable = False
                            break
            else:
                mergable = False
            if mergable:
                key_and_mask = info_by_app_vertex[app_vertex]
                table.add_multicast_routing_entry(MulticastRoutingEntry(
                    routing_entry_key=key_and_mask.key_combo,
                    defaultable=False, mask=key_and_mask.mask,
                    link_ids=first_entry.link_ids,
                    processor_ids=first_entry.processor_ids))
            else:
                for partition in partitions_by_app_vertex[app_vertex]:
                    r_info = routing_infos.get_routing_info_from_partition(partition)
                    entry = partitions_in_table[partition]
                    for key_and_mask in r_info.keys_and_masks:
                        table.add_multicast_routing_entry(MulticastRoutingEntry(
                            routing_entry_key=key_and_mask.key_combo,
                            defaultable=entry.defaultable, mask=key_and_mask.mask,
                            link_ids=entry.link_ids,
                            processor_ids=entry.processor_ids))
        return table
