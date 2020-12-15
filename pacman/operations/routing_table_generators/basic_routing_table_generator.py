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


class BasicRoutingTableGenerator(object):
    """ An basic algorithm that can produce routing tables
    """

    __slots__ = []

    def __call__(self, routing_infos, routing_table_by_partitions, machine):
        """
        :param RoutingInfo routing_infos:
        :param MulticastRoutingTableByPartition routing_table_by_partitions:
        :param ~spinn_machine.Machine machine:
        :rtype: MulticastRoutingTables
        """
        progress = ProgressBar(machine.n_chips, "Generating routing tables")
        routing_tables = MulticastRoutingTables()
        for chip in progress.over(machine.chips):
            partitions_in_table = routing_table_by_partitions.\
                get_entries_for_router(chip.x, chip.y)
            if partitions_in_table:
                routing_tables.add_routing_table(self._create_routing_table(
                    chip, partitions_in_table, routing_infos))

        return routing_tables

    def _create_routing_table(self, chip, partitions_in_table, routing_infos):
        """
        :param ~spinn_machine.Chip chip:
        :param partitions_in_table:
        :type partitions_in_table:
            dict(AbstractSingleSourcePartition,
            MulticastRoutingTableByPartitionEntry)
        :param RoutingInfo routing_infos:
        :rtype: MulticastRoutingTable
        """
        table = UnCompressedMulticastRoutingTable(chip.x, chip.y)
        for partition in partitions_in_table:
            r_info = routing_infos.get_routing_info_from_partition(partition)
            entry = partitions_in_table[partition]
            for key_and_mask in r_info.keys_and_masks:
                table.add_multicast_routing_entry(
                    self.__create_entry(key_and_mask, entry))
        return table

    @staticmethod
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
