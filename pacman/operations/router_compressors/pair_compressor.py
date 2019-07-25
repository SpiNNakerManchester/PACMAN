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

try:
    from collections.abc import defaultdict
except ImportError:
    from collections import defaultdict
from pacman.model.routing_tables import (
    MulticastRoutingTable, MulticastRoutingTables)

from .abstract_compressor import AbstractCompressor
from .entry import Entry


class PairCompressor(AbstractCompressor):

    __slots__ = [
        #X Dict (by spinnaker_route) (for current chip)
        #X   of entries represented as (key, mask, defautible)
        "_all_entries",
    ]

    def find_merge(self, an_entry, route_entries):
        for another in route_entries:
            m_key, m_mask, defaultable = self.merge(an_entry, another)
            ok = True
            for route in self._all_entries:
                for check in self._all_entries[route]:
                    if self.intersect(check.key, check.mask, m_key, m_mask):
                        ok = False
                        break
            if ok:
                route_entries.remove(another)
                return Entry(
                     m_key, m_mask, defaultable, an_entry.spinnaker_route)
        return None

    def compress_by_route(self, route_entries):
        results = []
        while len(route_entries) > 1:
            an_entry = route_entries.pop()
            merged = self.find_merge(an_entry, route_entries)
            if merged is None:
                results.append(an_entry)
            else:
                route_entries.append(merged)

        if len(route_entries) == 1:
            results.append(route_entries.pop())

        return results

    def compress_table(self, router_table):
        # Split the entries into buckets based on spinnaker_route

        self._all_entries = defaultdict(list)
        for entry in router_table.multicast_routing_entries:
            self._all_entries[entry.spinnaker_route].append(
                Entry.from_MulticastRoutingEntry(entry))

        results = []
        all_routes = list(self._all_entries)
        for spinnaker_route in all_routes:
            if len(self._all_entries[spinnaker_route]) == 1:
                results.extend(self._all_entries.pop(spinnaker_route))

        complex_routes = sorted(
            list(self._all_entries),
            key=lambda x: len(self._all_entries[x]) + 1/(self._all_entries[x][0].spinnaker_route+1),
            reverse=False)
        for spinnaker_route in complex_routes:
            compressed = self.compress_by_route(
                self._all_entries.pop(spinnaker_route))
            results.extend(compressed)

        if len(results) > self.MAX_SUPPORTED_LENGTH:
            self._problems += "(x:{},y:{})={} ".format(
                router_table.x, router_table.y, len(results))
        return results

