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
from typing import FrozenSet, Iterable, Optional, Union
from spinn_utilities.log import FormatAdapter
from pacman.exceptions import (
    PacmanConfigurationException, PacmanInvalidParameterException)

log = FormatAdapter(logging.getLogger(__name__))

_INCOMING_LINK_MASK = 0x07000000
_INCOMING_LINK_SHIFT = 24
_INCOMING_PROC_MASK = 0xF8000000
_INCOMING_PROC_SHIFT = 27
_OUTGOING_LINKS_MASK = 0x0000003F
_OUTGOING_LINK_1 = 0x00000001
_OUTGOING_PROCS_MASK = 0x00FFFFC0
_OUTGOING_PROC_1 = 0x00000040
_SPINNAKER_ROUTE_MASK = _OUTGOING_LINKS_MASK | _OUTGOING_PROCS_MASK
_COMPARE_MASK = _INCOMING_LINK_MASK | _SPINNAKER_ROUTE_MASK
_N_PROCS = 18
_N_LINKS = 6


class MulticastRoutingTableByPartitionEntry(object):
    """
    An entry in a path of a multicast route.
    """

    __slots__ = (
        # pylint: disable=wrong-spelling-in-comment
        # Entry made up of bits as follows:
        # | IL = 6 bits | IP = 1 bit | OL = 6 bits | OP = 18 bits |
        # IL = incoming link id
        # IP = whether the source is a processor or not
        # OL = outgoing links
        # OP = outgoing processors
        "_links_and_procs", )

    def __init__(self, out_going_links: Union[int, Iterable[int], None],
                 outgoing_processors: Union[int, Iterable[int], None],
                 incoming_processor: Optional[int] = None,
                 incoming_link: Optional[int] = None):
        """
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
        :raises PacmanInvalidParameterException:
        """
        self._links_and_procs = 0
        if isinstance(out_going_links, int):
            self.__set_outgoing_links([out_going_links])
        elif out_going_links is not None:
            self.__set_outgoing_links(out_going_links)

        if isinstance(outgoing_processors, int):
            self.__set_outgoing_procs([outgoing_processors])
        elif outgoing_processors is not None:
            self.__set_outgoing_procs(outgoing_processors)

        if incoming_link is not None and incoming_processor is not None:
            raise PacmanInvalidParameterException(
                "The incoming direction for a path can only be from either "
                "one link or one processors, not both",
                str(incoming_link), str(incoming_processor))
        if incoming_processor is not None:
            self.__set_incoming_proc(incoming_processor)
        elif incoming_link is not None:
            self.__set_incoming_link(incoming_link)

    def __set_incoming_link(self, link: int):
        if link > _N_LINKS:
            raise ValueError(f"Link {link} > {_N_LINKS}")
        # Add one so that 0 means not set
        self._links_and_procs |= (link + 1) << _INCOMING_LINK_SHIFT

    def __set_incoming_proc(self, proc: int):
        if proc > _N_PROCS:
            raise ValueError(f"Processor {proc} > {_N_PROCS}")
        # Add one so that 0 means not set
        self._links_and_procs |= (proc + 1) << _INCOMING_PROC_SHIFT

    def __set_outgoing_links(self, links: Iterable[int]):
        for link in links:
            if link > _N_LINKS:
                raise ValueError(f"Link {link} > {_N_LINKS}")
            self._links_and_procs |= _OUTGOING_LINK_1 << link

    def __set_outgoing_procs(self, procs: Iterable[int]):
        for proc in procs:
            if proc > _N_PROCS:
                raise ValueError(f"Processor {proc} > {_N_PROCS}")
            self._links_and_procs |= _OUTGOING_PROC_1 << proc

    @property
    def processor_ids(self) -> FrozenSet[int]:
        """
        The destination processors of the entry.

        :rtype: frozenset(int)
        """
        return frozenset(i for i in range(_N_PROCS)
                         if self._links_and_procs & (_OUTGOING_PROC_1 << i))

    @property
    def link_ids(self) -> FrozenSet[int]:
        """
        The destination links of the entry.

        :rtype: frozenset(int)
        """
        return frozenset(i for i in range(_N_LINKS)
                         if self._links_and_procs & (_OUTGOING_LINK_1 << i))

    @property
    def incoming_link(self) -> Optional[int]:
        """
        The source link for this path entry.

        :rtype: int or None
        """
        link = ((self._links_and_procs & _INCOMING_LINK_MASK) >>
                _INCOMING_LINK_SHIFT)
        if link == 0:
            return None
        # Subtract 1 as 0 means not set
        return link - 1

    @incoming_link.setter
    def incoming_link(self, incoming_link: int):
        if self.incoming_processor is not None:
            raise PacmanConfigurationException(
                f"Entry already has an incoming processor "
                f"{self.incoming_processor}")
        self_link = self.incoming_link
        if self_link is not None and self_link != incoming_link:
            raise PacmanConfigurationException(
                f"Entry already has an incoming link {self_link}")
        self.__set_incoming_link(incoming_link)

    @property
    def incoming_processor(self) -> Optional[int]:
        """
        The source processor.

        :rtype: int or None
        """
        proc = ((self._links_and_procs & _INCOMING_PROC_MASK) >>
                _INCOMING_PROC_SHIFT)
        if proc == 0:
            return None
        # Subtract 1 as 0 means not set
        return proc - 1

    @incoming_processor.setter
    def incoming_processor(self, incoming_processor: int):
        if self.incoming_link is not None:
            raise PacmanConfigurationException(
                f"Entry already has an incoming link {self.incoming_link}")
        self_proc = self.incoming_processor
        if self_proc is not None and self_proc != incoming_processor:
            raise PacmanConfigurationException(
                f"Entry already has an incoming processor {self_proc}")
        self.__set_incoming_proc(incoming_processor)

    @property
    def defaultable(self) -> bool:
        """
        The defaultable status of the entry.

        :rtype: bool
        """
        if self.incoming_processor is not None:
            return False
        in_link = self.incoming_link
        if in_link is None:
            return False
        out_links = self.link_ids
        if len(out_links) != 1:
            return False
        if self.processor_ids:
            return False
        out_link = next(iter(out_links))
        return ((in_link + 3) % 6) == out_link

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

        # validate incoming
        try:
            in_proc = self.__merge_none_or_equal(
                self.incoming_processor, other.incoming_processor,
                "incoming_processor")
            in_link = self.__merge_none_or_equal(
                self.incoming_link, other.incoming_link, "incoming_link")
            if in_proc is not None and in_link is not None:
                raise PacmanInvalidParameterException(
                    "other", "merge error",
                    f"Cannot merge {other} and {self}: both incoming processor"
                    " and link are set")
        except PacmanInvalidParameterException as e:
            log.error("Error merging entry {} into {}", other, self)
            raise e

        # Set the value directly as faster
        entry = MulticastRoutingTableByPartitionEntry(None, None)
        entry._links_and_procs = self._links_and_procs | other._links_and_procs
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
        return ((self._links_and_procs & _COMPARE_MASK) ==
                (entry._links_and_procs & _COMPARE_MASK))

    @property
    def spinnaker_route(self) -> int:
        """
        The masked routes

        :rtype: int
        """
        return self._links_and_procs & _SPINNAKER_ROUTE_MASK
