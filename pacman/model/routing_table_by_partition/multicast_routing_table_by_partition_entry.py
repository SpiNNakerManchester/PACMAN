# Copyright (c) 2015 The University of Manchester
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
from __future__ import annotations
import logging
from typing import Iterable, Optional, Union
from spinn_utilities.log import FormatAdapter
from spinn_machine.base_multicast_routing_entry import (
    BaseMulticastRoutingEntry)
from pacman.exceptions import (PacmanInvalidParameterException)

log = FormatAdapter(logging.getLogger(__name__))


class MulticastRoutingTableByPartitionEntry(BaseMulticastRoutingEntry):
    """
    An entry in a path of a multicast route.
    """

    __slots__ = ["_defaultable"]

    def __init__(self, out_going_links: Union[int, Iterable[int], None],
                 outgoing_processors: Union[int, Iterable[int], None],
                 incoming_processor: Optional[int] = None,
                 incoming_link: Optional[int] = None,
                 spinnaker_route: Optional[int] = None):
        """
        .. note::
            If a spinnaker_route is provided the out_going_links and
            outgoing_processors parameters are ignored.

        :param out_going_links:
            the edges this path entry goes down, each of which is between
            0 and 5
        :type out_going_links: int or iterable(int) or None
        :param outgoing_processors:
            the processors this path entry goes to, each of which is between
            0 and 17
        :type outgoing_processors: int or iterable(int) or None
        :param int incoming_processor:
            the direction this entry came from (between 0 and 17)
        :param int incoming_link:
            the direction this entry came from in link (between 0 and 5)
        :param spinnaker_route:
            The processor_ids and link_ids expressed as a single int.
        :type spinnaker_route: int or None

        :raises PacmanInvalidParameterException:
        """
        super().__init__(
            outgoing_processors, out_going_links,
            spinnaker_route=spinnaker_route)

        if incoming_processor is not None:
            self._defaultable = False
        elif incoming_link is None:
            self._defaultable = False
        else:
            # defaultable if the output route is exactly the inverse of input
            invert_link = ((incoming_link + 3) % 6)
            # as it is faster to go from a link to a spinnaker route
            self._defaultable = self._calc_spinnaker_route(
                None, invert_link) == self.spinnaker_route

    @property
    def defaultable(self) -> bool:
        """
        The defaultable status of the entry.

        :rtype: bool
        """
        return self._defaultable

    def merge_entry(self, other: MulticastRoutingTableByPartitionEntry) -> \
            MulticastRoutingTableByPartitionEntry:
        """
        Merges the another entry with this one and returns a new
        MulticastRoutingTableByPartitionEntry

        :param MulticastRoutingTableByPartitionEntry other:
            the entry to merge into this one
        :return: a merged MulticastRoutingTableByPartitionEntry
        :raises PacmanInvalidParameterException:
        """
        # pylint:disable=protected-access
        if not isinstance(other, MulticastRoutingTableByPartitionEntry):
            raise PacmanInvalidParameterException(
                "other", "type error",
                "The other parameter is not an instance of "
                "MulticastRoutingTableByPartitionEntry, and therefore cannot "
                "be merged.")

        if (self.defaultable == other.defaultable and
                self.spinnaker_route == other.spinnaker_route):
            return self

        # init checks if both incoming values are not None
        return MulticastRoutingTableByPartitionEntry(
            None, None,
            spinnaker_route=self.spinnaker_route | other.spinnaker_route)

    def __repr__(self) -> str:
        repr = (f"{{{', '.join(map(str, self.link_ids))}}}:"
                f"{{{', '.join(map(str, self.processor_ids))}}}")
        if self._defaultable:
            repr += ("defaultable")
        return repr
