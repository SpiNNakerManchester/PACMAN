from spinn_utilities.progress_bar import ProgressBar
from spinn_utilities.ordered_default_dict import DefaultOrderedDict
from spinn_machine import MulticastRoutingEntry
from pacman.model.routing_tables import (
    UnCompressedMulticastRoutingTable, MulticastRoutingTables)


class SharedEntry(object):
    slots = [

        # the edges this path entry goes down
        "link_ids",

        # the processors this path entry goes to
        "processor_ids",

        "defaultable"
        ]

    def __init__(self, entry):
        self.link_ids = entry.link_ids
        self.processor_ids = entry.processor_ids
        self.defaultable = entry.defaultable

    def still_defaultable(self, entry):
        self.defaultable = self.defaultable & entry.defaultable


class ZonedRoutingTableGenerator(object):
    """ An basic algorithm that can produce routing tables
    """

    __slots__ = []

    def __call__(
            self, routing_infos, routing_table_by_partitions, machine,
            graph_mapper, info_by_app_vertex):
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
                    chip, partitions_in_table, routing_infos, graph_mapper,
                    info_by_app_vertex))

        return routing_tables

    def _create_routing_table(self, chip, partitions_in_table, routing_infos,
                              graph_mapper, info_by_app_vertex):
        table = UnCompressedMulticastRoutingTable(chip.x, chip.y)
        partitions_by_app_vertex = DefaultOrderedDict(set)
        for partition in partitions_in_table:
            machine_vertex = partition.pre_vertex
            app_vertex = graph_mapper.get_application_vertex(machine_vertex)
            partitions_by_app_vertex[app_vertex].add(partition)
        for app_vertex in partitions_by_app_vertex:
            if app_vertex in info_by_app_vertex:
                shared_entry = self._find_shared_entry(
                    partitions_by_app_vertex[app_vertex], partitions_in_table)
            else:
                shared_entry = None
            if shared_entry is None:
                self._add_partition_based(
                    partitions_by_app_vertex[app_vertex], routing_infos,
                    partitions_in_table, table)
            else:
                self._add_key_and_mask(
                    info_by_app_vertex[app_vertex], shared_entry, table)
        return table

    def _find_shared_entry(self, partitions, partitions_in_table):
        shared_entry = None
        for partition in partitions:
            entry = partitions_in_table[partition]
            if shared_entry is None:
                shared_entry = SharedEntry(entry)
            else:
                if shared_entry.link_ids != entry.link_ids:
                    return None
                if shared_entry.processor_ids != entry.processor_ids:
                    return None
                shared_entry.still_defaultable(entry)
        return shared_entry

    def _add_partition_based(
            self, partitions, routing_infos, partitions_in_table, table):
        for partition in partitions:
            r_info = routing_infos.get_routing_info_from_partition(partition)
            entry = partitions_in_table[partition]
            for key_and_mask in r_info.keys_and_masks:
                self._add_key_and_mask(key_and_mask, entry, table)

    def _add_key_and_mask(self, key_and_mask, entry, table):
        table.add_multicast_routing_entry(MulticastRoutingEntry(
            routing_entry_key=key_and_mask.key_combo,
            defaultable=entry.defaultable, mask=key_and_mask.mask,
            link_ids=entry.link_ids,
            processor_ids=entry.processor_ids))
