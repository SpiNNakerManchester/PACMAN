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
        :param MulticastRoutingEntry mre:
        :rtype: Entry
        """
        # Yes I know using _params is ugly but this is for speed
        return Entry(
            mre._routing_entry_key, mre._mask, mre._defaultable,
            mre._spinnaker_route)

    def to_MulticastRoutingEntry(self):
        """
        :rtype: MulticastRoutingEntry
        """
        return MulticastRoutingEntry(
            self.key, self.mask, defaultable=self.defaultable,
            spinnaker_route=self.spinnaker_route)
