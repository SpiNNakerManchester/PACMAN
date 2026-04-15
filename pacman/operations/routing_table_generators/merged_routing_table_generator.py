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
from typing import (
    Dict, Iterable, List, Optional, Tuple, TypeVar, Generic)
from spinn_utilities.progress_bar import ProgressBar
from spinn_machine import MulticastRoutingEntry, RoutingEntry
from pacman.data import PacmanDataView
from pacman.model.routing_tables import (
    UnCompressedMulticastRoutingTable, MulticastRoutingTables)
from pacman.model.graphs.application import ApplicationVertex
from pacman.model.routing_info import (
    RoutingInfo, AppVertexRoutingInfo, MachineVertexRoutingInfo)
from pacman.model.graphs import AbstractVertex
from pacman.model.graphs.machine.machine_vertex import MachineVertex
from pacman.model.routing_info.base_key_and_mask import BaseKeyAndMask

#: :meta private:
E = TypeVar("E")


class _IteratorWithNext(Generic[E]):
    """
    An iterator wrapper which allows peek
    """

    def __init__(self, iterable: Iterable[E]):
        """
        :param iterable: iterable  to be wrapped
        """
        self.__iterator = iter(iterable)
        try:
            self.__next: Optional[E] = next(self.__iterator)
            self.__has_next = True
        except StopIteration:
            self.__next = None
            self.__has_next = False

    def peek(self) -> Optional[E]:
        """
        :returns: The Element if any that would be returned by a pop call
        """
        return self.__next

    @property
    def has_next(self) -> bool:
        """
        True if there is another element for Peek or Pop to return
        """
        return self.__has_next

    def pop(self) -> E:
        """
        :returns: The next element available.
        :raises: StopIteration if there is not more element available
        """
        if not self.__has_next:
            raise StopIteration
        nxt = self.__next
        assert nxt is not None
        try:
            self.__next = next(self.__iterator)
            self.__has_next = True
        except StopIteration:
            self.__next = None
            self.__has_next = False
        return nxt


def merged_routing_table_generator() -> MulticastRoutingTables:
    """
    Creates routing entries by merging adjacent entries from the same
    application vertex when possible.

    :returns: The merged routing tables.
    """
    routing_table_by_partitions = (
        PacmanDataView.get_routing_table_by_partition())
    routing_infos = PacmanDataView.get_routing_infos()
    progress = ProgressBar(
        routing_table_by_partitions.n_routers, "Generating routing tables")
    routing_tables = MulticastRoutingTables()
    for x, y in progress.over(routing_table_by_partitions.get_routers()):
        parts = routing_table_by_partitions.get_entries_for_router(x, y)
        if parts is None:
            continue
        routing_tables.add_routing_table(__create_routing_table(
            x, y, parts, routing_infos))

    return routing_tables


def __create_routing_table(
        x: int, y: int,
        partitions_in_table: Dict[Tuple[AbstractVertex, str],
                                  RoutingEntry],
        routing_info: RoutingInfo) -> UnCompressedMulticastRoutingTable:
    table = UnCompressedMulticastRoutingTable(x, y)
    sources_by_key_mask: Dict[BaseKeyAndMask,
                              Tuple[AbstractVertex, str]] = dict()
    iterator = _IteratorWithNext(partitions_in_table.items())
    while iterator.has_next:
        (vertex, part_id), entry = iterator.pop()
        r_info = routing_info.get_info_from(
            vertex, part_id)

        if r_info.key_and_mask in sources_by_key_mask:
            if (sources_by_key_mask[r_info.key_and_mask] != (vertex, part_id)):
                raise KeyError(
                    f"Source {vertex}, {part_id} is trying to "
                    f"send to the same key and mask as "
                    f"{sources_by_key_mask[r_info.key_and_mask]}")
        else:
            sources_by_key_mask[r_info.key_and_mask] = (
                vertex, part_id)

        # If we have an application vertex, just put the entry in and move on
        if isinstance(vertex, ApplicationVertex):
            table.add_multicast_routing_entry(
                MulticastRoutingEntry(
                    r_info.key, r_info.mask, entry))
            continue
        # Otherwise it has to be a machine vertex...
        assert isinstance(vertex, MachineVertex)
        assert isinstance(r_info, MachineVertexRoutingInfo)

        # If there is no application vertex, just add the entry
        if vertex.app_vertex is None:
            table.add_multicast_routing_entry(
                MulticastRoutingEntry(r_info.key, r_info.mask, entry))
            continue

        # This has to be AppVertexRoutingInfo!
        app_r_info = routing_info.get_info_from(
            vertex.app_vertex, part_id)
        assert isinstance(app_r_info, AppVertexRoutingInfo)

        # Get the entries to merge
        entries: List[Tuple[
            RoutingEntry, MachineVertexRoutingInfo]] = [(entry, r_info)]
        while __match(iterator, vertex, part_id, r_info, entry, routing_info,
                      app_r_info):
            (vertex, part_id), entry = iterator.pop()
            assert isinstance(vertex, MachineVertex)
            r_info = routing_info.get_info_from(
                vertex, part_id)
            if r_info is not None:
                assert isinstance(r_info, MachineVertexRoutingInfo)
                entries.append((entry, r_info))

        # Now attempt to merge sources together as much as possible
        for mrentry in __merged_keys_and_masks(app_r_info, entries):
            table.add_multicast_routing_entry(mrentry)

    return table


def __match(
        iterator: _IteratorWithNext[
            Tuple[Tuple[AbstractVertex, str], RoutingEntry]],
        vertex: MachineVertex,
        part_id: str, r_info: MachineVertexRoutingInfo, entry:  RoutingEntry,
        routing_info:  RoutingInfo,
        app_r_info: AppVertexRoutingInfo) -> bool:
    if not iterator.has_next:
        return False
    if r_info.mask != app_r_info.machine_mask:
        return False
    peeked = iterator.peek()
    assert peeked is not None
    (next_vertex, next_part_id), next_entry = peeked
    if isinstance(next_vertex, ApplicationVertex):
        return False
    if part_id != next_part_id:
        return False
    if __mask_has_holes(r_info.mask):
        return False
    next_r_info = routing_info.get_info_from(
        next_vertex, next_part_id)
    assert isinstance(next_r_info, MachineVertexRoutingInfo)
    if next_r_info.index != r_info.index + 1:
        return False
    app_src = vertex.app_vertex
    assert isinstance(next_vertex, MachineVertex)
    next_app_src = next_vertex.app_vertex
    return (next_app_src == app_src and
            entry.spinnaker_route == next_entry.spinnaker_route)


def __mask_has_holes(mask: int) -> bool:
    """
    Detect if the mask has a "hole" somewhere other than at the bottom.

    :param mask: The mask to check
    """
    # The mask is inverted and then add 1.  If this number is a power of 2,
    # the mask doesn't have holes
    inv_mask = (~mask & 0xFFFFFFFF) + 1
    # a & ~a == 0 if a is a power of 2
    return (inv_mask & (inv_mask - 1)) != 0


def __merged_keys_and_masks(
        app_r_info: AppVertexRoutingInfo,
        entries: List[Tuple[RoutingEntry, MachineVertexRoutingInfo]]
        ) -> Iterable[MulticastRoutingEntry]:
    if not entries:
        return
    (entry, r_info) = entries[0]
    if len(entries) == 1:
        yield MulticastRoutingEntry(r_info.key, r_info.mask, entry)
    else:
        yield from app_r_info.merge_machine_entries(entries)
