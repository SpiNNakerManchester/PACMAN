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

"""Data structures for the definition of SpiNNaker routing tables.

Based on
https://github.com/project-rig/rig/blob/master/rig/routing_table/entries.py
"""


class RoutingTableEntry(object):
    """
    Representing a single routing entry in a SpiNNaker routing table.

    Similar to to SpiNNaker route but without the parameter protection which
    speeds frequent access.
    """

    _slots__ = [
        # int value representing The set of destinations a packet should be
        # routed to where each element in the set is a value from the
        # enumeration
        "spinnaker_route",
        # 32-bit unsigned integer routing key to match after applying the mask.
        "key",
        # 32-bit unsigned integer mask to apply to keys of packets arriving at
        # the router.
        "mask",
        # bool value to say if the route is defaultable
        "defaultable"]

    def __init__(self, spinnaker_route, key, mask, defaultable):
        self.spinnaker_route = spinnaker_route
        self.key = key
        self.mask = mask
        self.defaultable = defaultable

    def __str__(self):
        # If no sources then don't display sources
        return "key:{} mask:{} route:{} defaultable:{}".format(
            self.key, self.mask, self.spinnaker_route, self.defaultable)
