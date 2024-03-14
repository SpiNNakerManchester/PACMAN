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
from spinn_machine import Router
from spinn_machine.base_multicast_routing_entry import (
    BaseMulticastRoutingEntry)
from pacman.exceptions import (
    PacmanConfigurationException, PacmanInvalidParameterException)

log = FormatAdapter(logging.getLogger(__name__))


class MulticastRoutingTableByPartitionEntry(BaseMulticastRoutingEntry):
    """
    An entry in a path of a multicast route.
    """

    __slots__ = ["_defaultable", "_incoming"]

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

        self._incoming = 0
        if incoming_link is None:
            if incoming_processor is None:
                self._defaultable = False
            else:
                self.incoming_processor = incoming_processor
        else:
            if incoming_processor is None:
                self.incoming_link = incoming_link
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
        if 0 < self._incoming <= Router.MAX_LINKS_PER_ROUTER:
            return self._incoming - 1
        else:
            return None

    @incoming_link.setter
    def incoming_link(self, incoming_link: int):
        self.__set_incoming(incoming_link + 1)

    @property
    def incoming_processor(self) -> Optional[int]:
        """
        The source processor.

        :rtype: int or None
        """
        if self._incoming > Router.MAX_LINKS_PER_ROUTER:
            return self._incoming - Router.MAX_LINKS_PER_ROUTER - 1
        else:
            return None

    @incoming_processor.setter
    def incoming_processor(self, incoming_processor: int):
        self.__set_incoming(
            incoming_processor + Router.MAX_LINKS_PER_ROUTER + 1)
        self._defaultable = False

    def __set_incoming(self, incoming: int):
        if self._incoming == 0 or self._incoming == incoming:
            self._incoming = incoming
            if 0 < self._incoming <= Router.MAX_LINKS_PER_ROUTER:
                # Defaultable if the spinnaker route represents just this link
                route = self._calc_spinnaker_route(None, incoming - 1)
                self._defaultable = (route == self.spinnaker_route)
            else:
                # Not defaultable if no incoming or incoming is not a link
                self._defaultable = False
        else:
            self_proc = self.incoming_processor
            self_link = self.incoming_link
            if self_link is not None:
                raise PacmanConfigurationException(
                    f"Entry already has an incoming link {self.link}")
            elif self_proc is not None:
                raise PacmanConfigurationException(
                    f"Entry already has an incoming processor {self_proc}")
            else:
                raise PacmanConfigurationException(
                    f"Entry already has an unexpected incoming value "
                    f"{self._incoming}")

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

        # validate incoming
        if self._incoming == 0:
            incoming = other._incoming
        elif other._incoming == 0:
            incoming = self._incoming
        elif self._incoming == other._incoming:
            incoming = self._incoming
        else:
            log.error("Error merging entry {} into {}", other, self)
            raise PacmanInvalidParameterException(
                "incoming", other._incoming,
                "The two MulticastRoutingTableByPartitionEntry have "
                "different incomings, and so can't be merged")

        entry = MulticastRoutingTableByPartitionEntry(
            None, None,
            spinnaker_route=self.spinnaker_route | other.spinnaker_route)
        entry.__set_incoming(incoming)
        return entry

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
        return (self.spinnaker_route == entry.spinnaker_route)
