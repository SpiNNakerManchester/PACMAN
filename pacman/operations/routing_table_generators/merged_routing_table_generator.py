# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from spinn_utilities.progress_bar import ProgressBar
from spinn_machine import MulticastRoutingEntry
from pacman.data import PacmanDataView
from pacman.exceptions import PacmanRoutingException
from pacman.model.routing_tables import (
    UnCompressedMulticastRoutingTable, MulticastRoutingTables)
from pacman.model.graphs.application import ApplicationVertex


def merged_routing_table_generator():
    """
    Creates routing entries by merging adjacent entries from the same
    application vertex when possible.

    :rtype: MulticastRoutingTables
    """
    routing_table_by_partitions = (
        PacmanDataView.get_routing_table_by_partition())
    routing_infos = PacmanDataView.get_routing_infos()
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
        (vertex, part_id), entry = iterator.pop()
        r_info = routing_info.get_routing_info_from_pre_vertex(vertex, part_id)
        if r_info is None:
            raise PacmanRoutingException(
                f"Missing Routing information for {vertex}, {part_id}")
        entries = [(vertex, part_id, entry, r_info)]
        while __match(iterator, vertex, part_id, r_info, entry, routing_info):
            (vertex, part_id), entry = iterator.pop()
            r_info = routing_info.get_routing_info_from_pre_vertex(
                vertex, part_id)
            entries.append((vertex, part_id, entry, r_info))

        # Now attempt to merge sources together as much as possible
        for entry in __merged_keys_and_masks(entries, routing_info):
            table.add_multicast_routing_entry(entry)

    return table


def __match(iterator, vertex, part_id, r_info, entry, routing_info):
    if not iterator.has_next:
        return False
    if isinstance(vertex, ApplicationVertex):
        return False
    (next_vertex, next_part_id), next_entry = iterator.peek()
    if isinstance(next_vertex, ApplicationVertex):
        return False
    if part_id != next_part_id:
        return False
    if __mask_has_holes(r_info.mask):
        return False
    next_r_info = routing_info.get_routing_info_from_pre_vertex(
        next_vertex, next_part_id)
    if next_r_info is None:
        raise KeyError(
            f"No routing info found for {next_vertex}, {next_part_id}")
    if next_r_info.index != r_info.index + 1:
        return False
    app_src = vertex.app_vertex
    next_app_src = next_vertex.app_vertex
    return next_app_src == app_src and entry.has_same_route(next_entry)


def __mask_has_holes(mask):
    """
    Detect if the mask has a "hole" somewhere other than at the bottom.

    :param int mask: The mask to check
    :rtype: bool
    """
    # The mask is inverted and then add 1.  If this number is a power of 2,
    # the mask doesn't have holes
    inv_mask = (~mask & 0xFFFFFFFF) + 1
    # a & ~a == 0 if a is a power of 2
    return (inv_mask & (inv_mask - 1)) != 0


def __merged_keys_and_masks(entries, routing_info):
    if not entries:
        return
    (vertex, part_id, entry, r_info) = entries[0]
    if isinstance(vertex, ApplicationVertex) or len(entries) == 1:
        yield MulticastRoutingEntry(
            r_info.key, r_info.mask, defaultable=entry.defaultable,
            spinnaker_route=entry.spinnaker_route)
    else:
        app_r_info = routing_info.get_routing_info_from_pre_vertex(
            vertex.app_vertex, part_id)
        yield from app_r_info.merge_machine_entries(entries)


class _IteratorWithNext(object):

    def __init__(self, iterable):
        self.__iterator = iter(iterable)
        try:
            self.__next = next(self.__iterator)
            self.__has_next = True
        except StopIteration:
            self.__next = None
            self.__has_next = False

    def peek(self):
        return self.__next

    @property
    def has_next(self):
        return self.__has_next

    def pop(self):
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
