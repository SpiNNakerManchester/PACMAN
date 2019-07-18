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

from pacman.exceptions import PacmanAlreadyExistsException


class MulticastRoutingTables(object):
    """ Represents the multicast routing tables for a number of chips.
    """

    __slots__ = [
        # set that holds routing tables
        "_routing_tables",
        # dict of (x,y) -> routing table
        "_routing_tables_by_chip"
    ]

    def __init__(self, routing_tables=None):
        """
        :param routing_tables: The routing tables to add
        :type routing_tables: \
            iterable(:py:class:`pacman.model.routing_tables.MulticastRoutingTable`)
        :raise pacman.exceptions.PacmanAlreadyExistsException: \
            If any two routing tables are for the same chip
        """
        self._routing_tables = set()
        self._routing_tables_by_chip = dict()

        if routing_tables is not None:
            for routing_table in routing_tables:
                self.add_routing_table(routing_table)

    def add_routing_table(self, routing_table):
        """ Add a routing table

        :param routing_table: a routing table to add
        :type routing_table:\
            :py:class:`pacman.model.routing_tables.MulticastRoutingTable`
        :rtype: None
        :raise pacman.exceptions.PacmanAlreadyExistsException: \
            If a routing table already exists for the chip
        """
        if routing_table in self._routing_tables:
            raise PacmanAlreadyExistsException(
                "The Routing table {} has already been added to the collection"
                " before and therefore already exists".format(routing_table),
                str(routing_table))

        if (routing_table.x, routing_table.y) in self._routing_tables_by_chip:
            raise PacmanAlreadyExistsException(
                "The Routing table for chip {}:{} already exists in this "
                "collection and therefore is deemed an error to re-add it"
                .format(routing_table.x, routing_table.y), str(routing_table))
        self._routing_tables_by_chip[(routing_table.x, routing_table.y)] = \
            routing_table
        self._routing_tables.add(routing_table)

    @property
    def routing_tables(self):
        """ The routing tables stored within

        :return: an iterable of routing tables
        :rtype: \
            iterable(:py:class:`pacman.model.routing_tables.MulticastRoutingTable`)
        :raise None: does not raise any known exceptions
        """
        return self._routing_tables

    def get_routing_table_for_chip(self, x, y):
        """ Get a routing table for a particular chip

        :param x: The x-coordinate of the chip
        :type x: int
        :param y: The y-coordinate of the chip
        :type y: int
        :return: The routing table, or None if no such table exists
        :rtype:\
            :py:class:`pacman.model.routing_tables.MulticastRoutingTable`\
            or None
        :raise None: No known exceptions are raised
        """
        return self._routing_tables_by_chip.get((x, y), None)

    def __iter__(self):
        """ Iterator for the multicast routing tables stored within

        :return: iterator of multicast_routing_table
        """
        return iter(self._routing_tables)
