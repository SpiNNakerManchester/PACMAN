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
from typing import Dict, List, Optional
from spinn_utilities.progress_bar import ProgressBar
from spinn_machine import Chip, FixedRouteEntry
from pacman.data import PacmanDataView
from pacman.exceptions import (
    PacmanAlreadyExistsException, PacmanConfigurationException,
    PacmanRoutingException)


def fixed_route_router(destination_class: type) -> Dict[Chip, FixedRouteEntry]:
    """
    Runs the fixed route generator for all boards on machine.

    :param destination_class: the destination class to route packets to
    :type destination_class: type or tuple(type,...)
    :return: router tables for fixed route paths
    :rtype: dict(~spinn_machine.Chip, ~spinn_machine.FixedRouteEntry)
    :raises PacmanConfigurationException: if no placement processor found
    :raises PacmanRoutingException:
    :raises PacmanAlreadyExistsException:
    """
    router = _FixedRouteRouter(destination_class)
    return router.build_fixed_routes()


class _FixedRouteRouter(object):
    """
    Computes the fixed routes used to direct data out traffic to the
    board-local gatherer processors.
    """

    __slots__ = (
        "_destination_class", "_fixed_route_tables",
        "_machine")

    def __init__(self, destination_class: type):
        self._machine = PacmanDataView.get_machine()
        self._destination_class = destination_class
        self._fixed_route_tables: Dict[Chip, FixedRouteEntry] = dict()

    def build_fixed_routes(self) -> Dict[Chip, FixedRouteEntry]:
        """
        Runs the fixed route generator for all boards on machine.

        :return: router tables for fixed route paths
        :rtype: dict(~spinn_machine.Chip, ~spinn_machine.FixedRouteEntry)
        :raises PacmanConfigurationException: if no placement processor found
        :raises PacmanRoutingException:
        :raises PacmanAlreadyExistsException:
        """
        # handle per board
        with ProgressBar(len(self._machine.ethernet_connected_chips),
                         "Generating fixed router routes") as progress:
            for ethernet_chip in progress.over(
                    self._machine.ethernet_connected_chips):
                self._route_board(ethernet_chip)
        return self._fixed_route_tables

    __LINK_DIRECTIONS = (4, 3, 5, 2, 0, 1)

    def _route_board(self, ethernet_chip: Chip):
        """
        Handles this board through the quick routing process, based on a
        predefined routing table.

        :param ~spinn_machine.Chip ethernet_chip:
            the Ethernet-connected chip identifying the board
        :raises PacmanRoutingException:
        :raises PacmanAlreadyExistsException:
        """
        to_route = set(self._machine.get_chips_by_ethernet(
            ethernet_chip.x, ethernet_chip.y))

        # create terminal fixed route entry
        # locate where to put data on ethernet chip
        processor_id = self.__locate_destination(ethernet_chip)
        # build entry and add to table and add to tables
        self.__add_fixed_route_entry(ethernet_chip, [], [processor_id])
        routed = {ethernet_chip}
        to_route.remove(ethernet_chip)
        found = set()

        while to_route:
            # Make routes to already-routed chips
            for chip in to_route:
                # Check links starting with the most direct to 0,0
                for link_id in self.__LINK_DIRECTIONS:
                    # If potential destination is useful and exists
                    if self.__get_chip_over_link(chip, link_id) in routed and (
                            self._machine.is_link_at(chip.x, chip.y, link_id)):
                        # build entry and add to table and add to tables
                        self.__add_fixed_route_entry(chip, [link_id], [])
                        found.add(chip)
                        break
            if not found:
                # Chip not reachable from board root via on-board links
                raise PacmanRoutingException(
                    "Unable to do fixed point routing "
                    f"on {ethernet_chip.ip_address}.")
            to_route -= found
            routed |= found
            found.clear()

    def __get_chip_over_link(self, chip: Chip, link_id: int) -> Optional[Chip]:
        x, y = self._machine.xy_over_link(chip.x, chip.y, link_id)
        return self._machine.get_chip_at(x, y)

    def __add_fixed_route_entry(
            self, key: Chip, link_ids: List[int], processor_ids: List[int]):
        """
        :param tuple(int,int) key:
        :param list(int) link_ids:
        :param list(int) processor_ids:
        :raises PacmanAlreadyExistsException:
        """
        if key in self._fixed_route_tables:
            raise PacmanAlreadyExistsException(
                "fixed route entry", str(key))
        self._fixed_route_tables[key] = FixedRouteEntry(
            link_ids=link_ids, processor_ids=processor_ids)

    def __locate_destination(self, chip: Chip) -> int:
        """
        Locate destination vertex on an (Ethernet-connected) chip to send
        fixed data to.

        :param ~spinn_machine.Chip chip:
        :return: processor ID as a int
        :rtype: int
        :raises PacmanConfigurationException: if no placement processor found
        """
        for placement in PacmanDataView.iterate_placements_by_xy_and_type(
                chip.x, chip.y, self._destination_class):
            return placement.p
        raise PacmanConfigurationException(
            f"no destination vertex found on Ethernet chip {chip.x}:{chip.y}")
