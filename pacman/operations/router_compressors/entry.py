# Copyright (c) 2017-2023 The University of Manchester
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

from spinn_machine import MulticastRoutingEntry


class Entry(object):
    __slots__ = ["key", "mask", "defaultable", "spinnaker_route"]

    def __init__(self, key, mask, defaultable, spinnaker_route):
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

    def __str__(self):
        return "{} {} {}".format(self.key, self.mask, self.spinnaker_route)

    def __eq__(self, other):
        if not isinstance(other, Entry):
            return False
        return (self.key == other.key and self.mask == other.mask and
                self.spinnaker_route == other.spinnaker_route)

    @staticmethod
    def from_MulticastRoutingEntry(mre):
        """
        :param ~spinn_machine.MulticastRoutingEntry mre:
        :rtype: Entry
        """
        # Yes I know using _params is ugly but this is for speed
        # pylint:disable=protected-access
        return Entry(
            mre._routing_entry_key, mre._mask, mre._defaultable,
            mre._spinnaker_route)

    def to_MulticastRoutingEntry(self):
        """
        :rtype: ~spinn_machine.MulticastRoutingEntry
        """
        return MulticastRoutingEntry(
            self.key, self.mask, defaultable=self.defaultable,
            spinnaker_route=self.spinnaker_route)
