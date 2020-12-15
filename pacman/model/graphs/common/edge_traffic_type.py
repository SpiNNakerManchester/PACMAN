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

from enum import IntEnum


class EdgeTrafficType(IntEnum):
    """ Indicates the traffic type of an Edge in a graph
    """

    #: Edge communicates using multicast packets
    MULTICAST = 1
    #: Edge communicates using fixed route packets
    FIXED_ROUTE = 2
    #: Edge communicates using shared memory
    SDRAM = 3
