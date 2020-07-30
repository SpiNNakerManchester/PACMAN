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

    #: Traffic is via SpiNNaker multicast packets. General, but can only pass
    #: a very small amount of information per message.
    MULTICAST = 1
    #: Traffic is via SpiNNaker fixed route packets.
    #: Vertices must usually be on the same board; number of destinations is
    #: strictly constrained.
    FIXED_ROUTE = 2
    #: Traffic is via a region of SDRAM. Vertices must be on same chip.
    SDRAM = 3
