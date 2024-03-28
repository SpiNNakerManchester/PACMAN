# Copyright (c) 2016 The University of Manchester
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
from typing import Dict, Tuple
from spinn_utilities.progress_bar import ProgressBar
from spinn_machine import MulticastRoutingEntry, RoutingEntry
from pacman.data import PacmanDataView
from pacman.model.routing_tables import (
    UnCompressedMulticastRoutingTable, MulticastRoutingTables)
from pacman.model.graphs import AbstractVertex
from pacman.model.routing_info import RoutingInfo


def basic_routing_table_generator() -> MulticastRoutingTables:
    """
    An basic algorithm that can produce routing tables.

    :rtype: MulticastRoutingTables
    """
    routing_infos = PacmanDataView.get_routing_infos()
    routing_table_by_partitions = (
        PacmanDataView.get_routing_table_by_partition())
    progress = ProgressBar(
        routing_table_by_partitions.n_routers, "Generating routing tables")
    routing_tables = MulticastRoutingTables()
    for x, y in progress.over(routing_table_by_partitions.get_routers()):
        parts = routing_table_by_partitions.get_entries_for_router(x, y)
        # Should be there; skip if not
        if parts is None:
            continue
        routing_tables.add_routing_table(__create_routing_table(
            x, y, parts, routing_infos))

    return routing_tables


def __create_routing_table(
        x: int, y: int, partitions_in_table: Dict[
            Tuple[AbstractVertex, str], RoutingEntry],
        routing_infos: RoutingInfo):
    """
    :param int x:
    :param int y:
    :param partitions_in_table:
    :type partitions_in_table:
        dict(((ApplicationVertex or MachineVertex), str),
        RoutingEntry)
    :param RoutingInfo routing_infos:
    :rtype: MulticastRoutingTable
    """
    table = UnCompressedMulticastRoutingTable(x, y)
    for source_vertex, partition_id in partitions_in_table:
        r_info = routing_infos.get_routing_info_from_pre_vertex(
            source_vertex, partition_id)
        # Should be there; skip if not
        if r_info is None:
            continue
        entry = partitions_in_table[source_vertex, partition_id]
        table.add_multicast_routing_entry(MulticastRoutingEntry(
            routing_entry_key=r_info.key_and_mask.key_combo,
            mask=r_info.key_and_mask.mask, routing_entry=entry))

    return table
