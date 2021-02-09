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
import logging
from collections import defaultdict
from spinn_utilities.log import FormatAdapter
from pacman.exceptions import MinimisationFailedError
from .abstract_compressor import AbstractCompressor
from .entry import Entry
from spinn_utilities.overrides import overrides
logger = FormatAdapter(logging.getLogger(__file__))


class ClashCompressor(AbstractCompressor):
    __slots__ = [
        "_all_entries",
        "_max_clashes"
    ]

    def find_merge(self, an_entry, route_entries):
        """
        :param ~.Entry an_entry:
        :param list(Entry) route_entries:
        :rtype: ~.Entry or None
        """
        for another in route_entries:
            m_key, m_mask, defaultable = self.merge(an_entry, another)
            clashers = []
            for route in self._all_entries:
                for check in self._all_entries[route]:
                    if self.intersect(check.key, check.mask, m_key, m_mask):
                        if len(clashers) >= self._max_clashes:
                            break
                        clashers.append(check)
                if len(clashers) >= self._max_clashes:
                    break
            if len(clashers) == 0:
                route_entries.remove(another)
                return Entry(
                    m_key, m_mask, defaultable, an_entry.spinnaker_route)
            if len(clashers) <= self._max_clashes:
                for entry in clashers:
                    entry.clashes += 1
        return None

    def compress_by_route(self, route_entries):
        """
        :param list(~.Entry) route_entres:
        :rtype: list(~.Entry)
        """
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

    def compress_ignore_clashers(self, router_table, top_entries):
        """
        :param MulticastRoutingTable router_table:
        :param list(~.Entry) top_entries:
        :rtype: list(~.Entry)
        :raises MinimisationFailedError:
        """
        while True:
            self._all_entries = defaultdict(list)
            for mcr_entry in router_table.multicast_routing_entries:
                entry = Entry.from_MulticastRoutingEntry(mcr_entry)
                if entry not in top_entries:
                    self._all_entries[entry.spinnaker_route].append(entry)

            if len(top_entries) + \
                    len(self._all_entries) > self.MAX_SUPPORTED_LENGTH:
                raise MinimisationFailedError("Too many top entries")

            results = []
            all_routes = list(self._all_entries)
            for spinnaker_route in all_routes:
                if len(self._all_entries[spinnaker_route]) == 1:
                    results.extend(self._all_entries.pop(spinnaker_route))

            complex_routes = sorted(
                list(self._all_entries),
                key=lambda x: len(self._all_entries[x]) +
                1/(self._all_entries[x][0].spinnaker_route + 1),
                reverse=False)
            for spinnaker_route in complex_routes:
                compressed = self.compress_by_route(
                    self._all_entries.pop(spinnaker_route))
                results.extend(compressed)

            if len(top_entries) + len(results) < self._target_length:
                logger.info("success! {} {} {}",
                            len(top_entries) + len(results),
                            len(top_entries), len(results))
                answer = top_entries + results
                logger.info("Good Results {}", len(answer))
                return answer

            clashers = []
            for entry in results:
                if entry.clashes > 0:
                    clashers.append(entry)
            logger.info("{} ({},{},{})", len(top_entries) + len(results),
                        len(top_entries), len(results), len(clashers))

            if len(clashers) == 0:
                answer = top_entries + results
                logger.info("Best Results {}", len(answer))
                if len(answer) > self.MAX_SUPPORTED_LENGTH:
                    raise MinimisationFailedError("No clashers left")
                return answer

            clashers = sorted(clashers, key=lambda x: x.clashes, reverse=True)
            top_entries.extend(clashers[0:1])

    @overrides(AbstractCompressor.compress_table)
    def compress_table(self, router_table):
        # Split the entries into buckets based on spinnaker_route

        self._max_clashes = 1

        try:
            return self.compress_ignore_clashers(router_table, [])
        except Exception:  # pylint: disable=broad-except
            logger.exception("failed to compress table at {}:{}",
                             router_table.x, router_table.y)
            self._problems += "(x:{},y:{})={} ".format(
                router_table.x, router_table.y, router_table.number_of_entries)
        return []
