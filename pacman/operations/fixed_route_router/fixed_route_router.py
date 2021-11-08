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
from spinn_machine import FixedRouteEntry, Machine
from pacman.exceptions import (
    PacmanAlreadyExistsException, PacmanConfigurationException,
    PacmanRoutingException)

def fixed_route_router(machine, placements, destination_class):
    """ Runs the fixed route generator for all boards on machine

    :param ~spinn_machine.Machine machine: SpiNNMachine object
    :param Placements placements: placements object
    :param destination_class: the destination class to route packets to
    :type destination_class: type or tuple(type,...)
    :return: router tables for fixed route paths
    :rtype: dict(tuple(int,int), ~spinn_machine.FixedRouteEntry)
    :raises PacmanConfigurationException: if no placement processor found
    :raises PacmanRoutingException:
    :raises PacmanAlreadyExistsException:
    """
    router = _FixedRouteRouter()
    return router(machine, placements, destination_class)


class _FixedRouteRouter(object):
    """ Computes the fixed routes used to direct data out traffic to the
        board-local gatherer processors.
    """

    __slots__ = [
        "_destination_class", "_fixed_route_tables",
        "_machine", "_placements"]

    def __call__(self, machine, placements, destination_class):
        """ Runs the fixed route generator for all boards on machine

        :param ~spinn_machine.Machine machine: SpiNNMachine object
        :param Placements placements: placements object
        :param destination_class: the destination class to route packets to
        :type destination_class: type or tuple(type,...)
        :return: router tables for fixed route paths
        :rtype: dict(tuple(int,int), ~spinn_machine.FixedRouteEntry)
        :raises PacmanConfigurationException: if no placement processor found
        :raises PacmanRoutingException:
        :raises PacmanAlreadyExistsException:
        """
        # pylint: disable=attribute-defined-outside-init

        self._machine = machine
        self._destination_class = destination_class
        self._placements = placements
        self._fixed_route_tables = dict()

        progress = ProgressBar(
            len(machine.ethernet_connected_chips),
            "Generating fixed router routes")

        # handle per board
        for ethernet_chip in progress.over(machine.ethernet_connected_chips):
            self._do_fixed_routing(ethernet_chip)
        return self._fixed_route_tables

    def _do_fixed_routing(self, ethernet_connected_chip):
        """ Handles this board through the quick routing process, based on a\
            predefined routing table.

        :param ~spinn_machine.Chip ethernet_connected_chip:
            the Ethernet connected chip
        :raises PacmanRoutingException:
        :raises PacmanAlreadyExistsException:
        """
        eth_x = ethernet_connected_chip.x
        eth_y = ethernet_connected_chip.y

        to_route = set(
            self._machine.get_existing_xys_by_ethernet(eth_x, eth_y))
        routed = set()
        routed.add((eth_x, eth_y))
        to_route.remove((eth_x, eth_y))

        while len(to_route) > 0:
            found = []
            for x, y in to_route:
                # Check links starting with the most direct to 0,0
                for link_id in [4, 3, 5, 2, 0, 1]:
                    # Get protential destination
                    destination = self._machine.xy_over_link(x, y, link_id)
                    # If it is useful
                    if destination in routed:
                        # check it actually exits
                        if self._machine.is_link_at(x, y, link_id):
                            # build entry and add to table and add to tables
                            key = (x, y)
                            self.__add_fixed_route_entry(key, [link_id], [])
                            found.append(key)
                            break
            if len(found) == 0:
                raise PacmanRoutingException(
                    "Unable to do fixed point routing on {}.".format(
                        ethernet_connected_chip.ip_address))
            for key in found:
                to_route.remove(key)
                routed.add(key)

        # create final fixed route entry
        # locate where to put data on ethernet chip
        processor_id = self.__locate_destination(ethernet_connected_chip)
        # build entry and add to table and add to tables
        self.__add_fixed_route_entry((eth_x, eth_y), [], [processor_id])

    def __add_fixed_route_entry(self, key, link_ids, processor_ids):
        """
        :param tuple(int,int) key:
        :param list(int) link_ids:
        :param list(int) processor_ids:
        :raises PacmanAlreadyExistsException:
        """
        fixed_route_entry = FixedRouteEntry(
            link_ids=link_ids, processor_ids=processor_ids)
        if key in self._fixed_route_tables:
            raise PacmanAlreadyExistsException(
                "fixed route entry", str(key))
        self._fixed_route_tables[key] = fixed_route_entry

    def __locate_destination(self, chip):
        """ Locate destination vertex on (Ethernet-connected) chip to send
            fixed data to

        :param ~spinn_machine.Chip chip:
        :return: processor ID as a int
        :rtype: int
        :raises PacmanConfigurationException: if no placement processor found
        """
        x = chip.x
        y = chip.y
        for p in range(Machine.max_cores_per_chip()):
            # check if occupied and by the right vertex type
            if self._placements.is_processor_occupied(x, y, p) and isinstance(
                    self._placements.get_vertex_on_processor(x, y, p),
                    self._destination_class):
                return p
        raise PacmanConfigurationException(
            "no destination vertex found on Ethernet chip {}:{}".format(
                chip.x, chip.y))
