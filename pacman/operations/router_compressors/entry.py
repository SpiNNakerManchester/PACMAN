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


class Entry(object):
    __slots__ = ["key", "mask", "defaultable", "spinnaker_route"]

    def __init__(self, key, mask, defaultable, spinnaker_route):
        self.key = key
        self.mask = mask
        self.defaultable = defaultable
        self.spinnaker_route = spinnaker_route

    def __str__(self):
        return "{} {} {}".format(self.key, self.mask, self.spinnaker_route)
