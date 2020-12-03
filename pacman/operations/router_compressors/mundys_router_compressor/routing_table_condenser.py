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

from pacman.operations.router_compressors import (AbstractCompressor, Entry)
from .ordered_covering import minimise


class MundyRouterCompressor(AbstractCompressor):
    """ Compressor from rig that has been tied into the main tool chain stack.
    """

    __slots__ = []

    def __init__(self):
        super(MundyRouterCompressor, self).__init__(True)

    def compress_table(self, router_table):
        """
        :param UnCompressedMulticastRoutingTable router_table:
        :rtype: list(~pacman.operations.router_compressors.Entry)
        """
        # convert to rig inspired format
        entries = list()

        # handle entries
        for router_entry in router_table.multicast_routing_entries:
            # Add the new entry
            entries.append(Entry.from_MulticastRoutingEntry(router_entry))

        # compress the router entries
        compressed_router_table_entries = minimise(
            entries, self._target_length)
        return compressed_router_table_entries
