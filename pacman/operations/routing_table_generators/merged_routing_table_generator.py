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

from spinn_utilities.progress_bar import ProgressBar
from spinn_machine import MulticastRoutingEntry
from pacman.model.routing_tables import (
    UnCompressedMulticastRoutingTable, MulticastRoutingTables)
from pacman.model.graphs.application import ApplicationVertex


def merged_routing_table_generator(
        routing_infos, routing_table_by_partitions):
    """ Creates routing entries by merging adjacent entries from the same
        application vertex when possible.

    :param RoutingInfo routing_infos:
    :param MulticastRoutingTableByPartition routing_table_by_partitions:
    :param ~spinn_machine.Machine machine:
    :rtype: MulticastRoutingTables
    """
    progress = ProgressBar(
        routing_table_by_partitions.n_routers, "Generating routing tables")
    routing_tables = MulticastRoutingTables()
    for x, y in progress.over(routing_table_by_partitions.get_routers()):
        parts = routing_table_by_partitions.get_entries_for_router(x, y)
        routing_tables.add_routing_table(__create_routing_table(
            x, y, parts, routing_infos))

    return routing_tables


def __create_routing_table(x, y, partitions_in_table, routing_info):
    """
    :param int x:
    :param int y:
    :param partitions_in_table:
    :type partitions_in_table:
        dict(((ApplicationVertex or MachineVertex), str),
        MulticastRoutingTableByPartitionEntry)
    :param RoutingInfo routing_infos:
    :rtype: MulticastRoutingTable
    """
    table = UnCompressedMulticastRoutingTable(x, y)
    iterator = _IteratorWithNext(partitions_in_table.items())
    while iterator.has_next:
        (vertex, part_id), entry = iterator.next
        r_info = routing_info.get_routing_info_from_pre_vertex(vertex, part_id)
        if r_info is None:
            raise Exception(
                f"Missing Routing information for {vertex}, {part_id}")
        entries = [(vertex, part_id, entry, r_info)]
        while __match(iterator, vertex, part_id, r_info, entry, routing_info):
            (vertex, part_id), entry = iterator.next
            r_info = routing_info.get_routing_info_from_pre_vertex(
                vertex, part_id)
            entries.append((vertex, part_id, entry, r_info))

        # Now attempt to merge sources together as much as possible
        for entry in __merged_keys_and_masks(entries, routing_info):
            table.add_multicast_routing_entry(entry)

    for source_vertex, partition_id in partitions_in_table:
        entry = partitions_in_table[source_vertex, partition_id]

    return table


def __match(iterator, vertex, part_id, r_info, entry, routing_info):
    if not iterator.has_next:
        return False
    if isinstance(vertex, ApplicationVertex):
        return False
    (next_vertex, next_part_id), next_entry = iterator.peek
    if isinstance(next_vertex, ApplicationVertex):
        return False
    if part_id != next_part_id:
        return False
    next_r_info = routing_info.get_routing_info_from_pre_vertex(
        next_vertex, next_part_id)
    if next_r_info.index != r_info.index + 1:
        return False
    app_src = vertex.app_vertex
    next_app_src = next_vertex.app_vertex
    return next_app_src == app_src and entry.has_same_route(next_entry)


def __merged_keys_and_masks(entries, routing_info):
    if not entries:
        return
    (vertex, part_id, entry, r_info) = entries[0]
    if isinstance(vertex, ApplicationVertex) or len(entries) == 1:
        yield MulticastRoutingEntry(
            r_info.first_key, r_info.first_mask, defaultable=entry.defaultable,
            spinnaker_route=entry.spinnaker_route)
    else:
        app_r_info = routing_info.get_routing_info_from_pre_vertex(
            vertex.app_vertex, part_id)
        yield from app_r_info.merge_machine_entries(entries)


def __create_entry(key_and_mask, entry):
    """
    :param BaseKeyAndMask key_and_mask:
    :param MulticastRoutingTableByPartitionEntry entry:
    :rtype: MulticastRoutingEntry
    """
    return MulticastRoutingEntry(
        routing_entry_key=key_and_mask.key_combo,
        defaultable=entry.defaultable, mask=key_and_mask.mask,
        link_ids=entry.link_ids, processor_ids=entry.processor_ids)


class _IteratorWithNext(object):

    def __init__(self, iterable):
        self.__iterator = iter(iterable)
        try:
            self.__next = next(self.__iterator)
            self.__has_next = True
        except StopIteration:
            self.__next = None
            self.__has_next = False

    @property
    def peek(self):
        return self.__next

    @property
    def has_next(self):
        return self.__has_next

    @property
    def next(self):
        if not self.__has_next:
            raise StopIteration
        nxt = self.__next
        try:
            self.__next = next(self.__iterator)
            self.__has_next = True
        except StopIteration:
            self.__next = None
            self.__has_next = False
        return nxt
