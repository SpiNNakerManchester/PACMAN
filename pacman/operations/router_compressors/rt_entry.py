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
from __future__ import annotations
from spinn_machine import MulticastRoutingEntry


class RTEntry(object):
    """
    The internal representation of router table entries used by the router
    table compressors. Essentially a tuple and compacted version of
    :py:class:`~spinn_machine.MulticastRoutingEntry`.

    :param key: The key
    :type key: int
    :param mask: The mask
    :type mask: int
    :param defaultable: Whether the route may be handled by default routing
    :type defaultable: bool
    :param spinnaker_route: The route
    :type spinnaker_route: int
    :param key_mask: The key,mask pair
    :type key_mask: tuple(int,int)
    """
    __slots__ = ("key", "mask", "defaultable", "spinnaker_route", "key_mask")

    def __init__(self, key: int, mask: int, defaultable: bool,
                 spinnaker_route: int):
        """
        :param int key:
        :param int mask:
        :param bool defaultable:
        :param int spinnaker_route:
        """
        self.key = key
        self.mask = mask
        self.defaultable = defaultable
        self.spinnaker_route = spinnaker_route
        self.key_mask = (key, mask)

    def __str__(self):
        return f"{self.key} {self.mask} {self.spinnaker_route}"

    def __eq__(self, other):
        if not isinstance(other, RTEntry):
            return False
        return (self.key == other.key and self.mask == other.mask and
                self.spinnaker_route == other.spinnaker_route)

    @staticmethod
    def from_multicast_routing_entry(source: MulticastRoutingEntry) -> RTEntry:
        """
        :param ~spinn_machine.MulticastRoutingEntry source:
        :rtype: RTEntry
        """
        # Yes I know using _params is ugly but this is for speed
        # pylint:disable=protected-access
        return RTEntry(
            source._routing_entry_key, source._mask, source._defaultable,
            source._spinnaker_route)

    def to_multicast_routing_entry(self) -> MulticastRoutingEntry:
        """
        :rtype: ~spinn_machine.MulticastRoutingEntry
        """
        return MulticastRoutingEntry(
            self.key, self.mask, defaultable=self.defaultable,
            spinnaker_route=self.spinnaker_route)
