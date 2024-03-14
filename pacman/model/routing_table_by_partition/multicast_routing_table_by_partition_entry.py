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
from spinn_machine.constants import MAX_LINKS_PER_ROUTER
from spinn_machine.base_multicast_routing_entry import (
    BaseMulticastRoutingEntry)
from pacman.exceptions import (
    PacmanConfigurationException, PacmanInvalidParameterException)

log = FormatAdapter(logging.getLogger(__name__))


class MulticastRoutingTableByPartitionEntry(BaseMulticastRoutingEntry):
    """
    An entry in a path of a multicast route.
    """

    __slots__ = ["_incoming_processor", "_incoming_link"]

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

        self._incoming_link: Optional[int]
        self._incoming_processor: Optional[int]
        if incoming_link is None:
            self._incoming_link = None
            self._incoming_processor = incoming_processor
        else:
            if incoming_processor is None:
                self._incoming_link = incoming_link
                self._incoming_processor = None
            else:
                raise PacmanInvalidParameterException(
                    "The incoming direction for a path can only be from "
                    "either one link or one processors, not both",
                    str(incoming_link), str(incoming_processor))

    @property
    def incoming_link(self) -> Optional[int]:
        """
        The source link for this path entry.

        :rtype: int or None
        """
        return self._incoming_link

    @incoming_link.setter
    def incoming_link(self, incoming_link: int):
        if self._incoming_processor is not None:
            raise PacmanConfigurationException(
                f"Entry already has an incoming processor "
                f"{self._incoming_processor}")
        if (self._incoming_link is not None
                and self._incoming_link != incoming_link):
            raise PacmanConfigurationException(
                f"Entry already has an unexpected incoming value "
                f"{self._incoming}")
        self._incoming_link = incoming_link

    @property
    def incoming_processor(self) -> Optional[int]:
        """
        The source processor.

        :rtype: int or None
        """
        if self._incoming > MAX_LINKS_PER_ROUTER:
            return self._incoming - MAX_LINKS_PER_ROUTER - 1
        else:
            return None

    @incoming_processor.setter
    def incoming_processor(self, incoming_processor: int):
        if (self._incoming_processor is not None and
                self._incoming_processor != incoming_processor):
            raise PacmanConfigurationException(
                f"Entry already has an incoming processor "
                f"{self._incoming_processor}")
        if self._incoming_link is not None:
            raise PacmanConfigurationException(
                f"Entry already has an unexpected incoming value "
                f"{self._incoming}")
        self._incoming_processor = self._incoming_processor

    @property
    def defaultable(self) -> bool:
        """
        The defaultable status of the entry.

        :rtype: bool
        """
        # without an incoming link is is not defaultable
        if self._incoming_link is None:
            return False
        # defaultable if the output route is exactly the inverse of the input
        invert_link = ((self._incoming_li + 3) % 6)
        # as it is faster to go from a link to a spinnaker route
        return (self._calc_spinnaker_route(None, invert_link) ==
                self.spinnaker_route)

    @staticmethod
    def __merge_none_or_equal(p1, p2, name):
        if p1 is None:
            return p2
        if p2 is None or p2 == p1:
            return p1
        raise PacmanInvalidParameterException(
            name, "invalid merge",
            "The two MulticastRoutingTableByPartitionEntry have "
            "different " + name + "s, and so can't be merged")

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

        if self._incoming_processor is None:
            incoming_processor = other._incoming_processor
        elif (other._incoming_processor is None or
              self._incoming_processor == other._incoming_processor):
            incoming_processor = self._incoming_processor
        else:
            raise PacmanInvalidParameterException(
                "other", other,
                "The two MulticastRoutingTableByPartitionEntry have "
                "different incoming processors, and so can't be merged")

        if self._incoming_link is None:
            incoming_link = other._incoming_link
        elif (other._incoming_link is None or
              self._incoming_link == other._incoming_link):
            incoming_link = self._incoming_link
        else:
            raise PacmanInvalidParameterException(
                "other", other,
                "The two MulticastRoutingTableByPartitionEntry have "
                "different incoming links, and so can't be merged")

        # init checks if both incoming values are not None
        return MulticastRoutingTableByPartitionEntry(
            None, None, incoming_processor, incoming_link,
            spinnaker_route=self.spinnaker_route | other.spinnaker_route)

    def __repr__(self) -> str:
        return (f"{self.incoming_link}:{self.incoming_processor}:"
                f"{self.defaultable}:"
                f"{{{', '.join(map(str, self.link_ids))}}}:"
                f"{{{', '.join(map(str, self.processor_ids))}}}")

    def has_same_route(
            self, entry: MulticastRoutingTableByPartitionEntry) -> bool:
        """
        Checks if the two Entries have the same routes after applying mask

        :param  MulticastRoutingTableByPartitionEntry entry:
        :rtype: bool
        """
        # pylint:disable=protected-access
        # False if the outgoing processor of linsk are diffeent
        if self.spinnaker_route != entry.spinnaker_route:
            return False
        # True if the incoming link or processor is the same
        if self._incoming == entry._incoming:
            return True
        # True if both have an incoming processor even if different
        return (self._incoming > MAX_LINKS_PER_ROUTER and
                entry._incoming > MAX_LINKS_PER_ROUTER)
