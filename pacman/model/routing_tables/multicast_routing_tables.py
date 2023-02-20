# Copyright (c) 2014 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import gzip
from pacman.exceptions import PacmanAlreadyExistsException
from .uncompressed_multicast_routing_table import \
    UnCompressedMulticastRoutingTable
from spinn_machine import MulticastRoutingEntry


class MulticastRoutingTables(object):
    """ Represents the multicast routing tables for a number of chips.
    """

    __slots__ = [
        # dict of (x,y) -> routing table
        "_routing_tables_by_chip",
        # maximum value for number_of_entries in all tables
        "_max_number_of_entries"
    ]

    def __init__(self, routing_tables=None):
        """
        :param iterable(MulticastRoutingTable) routing_tables:
            The routing tables to add
        :raise PacmanAlreadyExistsException:
            If any two routing tables are for the same chip
        """
        self._routing_tables_by_chip = dict()
        self._max_number_of_entries = 0

        if routing_tables is not None:
            for routing_table in routing_tables:
                self.add_routing_table(routing_table)

    def add_routing_table(self, routing_table):
        """ Add a routing table

        :param MulticastRoutingTable routing_table: a routing table to add
        :rtype: None
        :raise PacmanAlreadyExistsException:
            If a routing table already exists for the chip
        """
        if (routing_table.x, routing_table.y) in self._routing_tables_by_chip:
            raise PacmanAlreadyExistsException(
                "The Routing table for chip {}:{} already exists in this "
                "collection and therefore is deemed an error to re-add it"
                .format(routing_table.x, routing_table.y), str(routing_table))
        self._routing_tables_by_chip[(routing_table.x, routing_table.y)] = \
            routing_table
        self._max_number_of_entries = max(
            self._max_number_of_entries, routing_table.number_of_entries)

    @property
    def routing_tables(self):
        """ The routing tables stored within

        :return: an iterable of routing tables
        :rtype: iterable(MulticastRoutingTable)
        :raise None: does not raise any known exceptions
        """
        return self._routing_tables_by_chip.values()

    @property
    def max_number_of_entries(self):
        """
        The maximumn number of multi-cast routing entries there are in any\
            multicast routing table

        Will return zero if there are no routing tables

        :rtype: int
        """
        return self._max_number_of_entries

    def get_routing_table_for_chip(self, x, y):
        """ Get a routing table for a particular chip

        :param int x: The x-coordinate of the chip
        :param int y: The y-coordinate of the chip
        :return: The routing table, or None if no such table exists
        :rtype: MulticastRoutingTable or None
        :raise None: No known exceptions are raised
        """
        return self._routing_tables_by_chip.get((x, y), None)

    def __iter__(self):
        """ Iterator for the multicast routing tables stored within

        :return: iterator of multicast_routing_table
        """
        return iter(self._routing_tables_by_chip.values())


def to_json(router_table):
    json_list = []
    for routing_table in router_table:
        json_routing_table = dict()
        json_routing_table["x"] = routing_table.x
        json_routing_table["y"] = routing_table.y
        entries = []
        for entry in routing_table.multicast_routing_entries:
            json_entry = dict()
            json_entry["key"] = entry.routing_entry_key
            json_entry["mask"] = entry.mask
            json_entry["defaultable"] = entry.defaultable
            json_entry["spinnaker_route"] = entry.spinnaker_route
            entries.append(json_entry)
        json_routing_table["entries"] = entries
        json_list.append(json_routing_table)
    return json_list


def from_json(j_router):
    if isinstance(j_router, str):
        if j_router.endswith(".gz"):
            with gzip.open(j_router) as j_file:
                j_router = json.load(j_file)
        else:
            with open(j_router, encoding="utf-8") as j_file:
                j_router = json.load(j_file)

    tables = MulticastRoutingTables()
    for j_table in j_router:
        table = UnCompressedMulticastRoutingTable(j_table["x"], j_table["y"])
        tables.add_routing_table(table)
        for j_entry in j_table["entries"]:
            table.add_multicast_routing_entry(MulticastRoutingEntry(
                j_entry["key"], j_entry["mask"],
                defaultable=j_entry["defaultable"],
                spinnaker_route=j_entry["spinnaker_route"]))
    return tables
