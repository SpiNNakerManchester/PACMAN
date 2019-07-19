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

from enum import Enum

DEFAULT_MASK = 0xfffff800  # DEFAULT LOCATION FOR THE APP MASK
BITS_IN_KEY = 32
BYTE_TO_WORD_MULTIPLIER = 4

CORES_PER_VIRTUAL_CHIP = 128

EDGES = Enum(
    value="EDGES",
    names=[("EAST", 0),
           ("NORTH_EAST", 1),
           ("NORTH", 2),
           ("WEST", 3),
           ("SOUTH_WEST", 4),
           ("SOUTH", 5)])
