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
FULL_MASK = 0xFFFFFFFF  # DEFAULT MASK FOR EVERYTHING

CORES_PER_VIRTUAL_CHIP = 128

EDGES = Enum(
    value="EDGES",
    names=[("EAST", 0),
           ("NORTH_EAST", 1),
           ("NORTH", 2),
           ("WEST", 3),
           ("SOUTH_WEST", 4),
           ("SOUTH", 5)])

#: How many bytes there are in a word
BYTES_PER_WORDS = 4

#: The number of bytes used by SARK per memory allocation
SARK_PER_MALLOC_SDRAM_USAGE = 2 * BYTES_PER_WORDS
