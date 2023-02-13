# Copyright (c) 2014-2023 The University of Manchester
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

from enum import Enum

DEFAULT_MASK = 0xfffff800  # DEFAULT LOCATION FOR THE APP MASK
BITS_IN_KEY = 32
FULL_MASK = 0xFFFFFFFF  # DEFAULT MASK FOR EVERYTHING

CORES_PER_VIRTUAL_CHIP = 128

BYTES_PER_WORD = 4

#: The number of bytes used by SARK per memory allocation
SARK_PER_MALLOC_SDRAM_USAGE = 2 * BYTES_PER_WORD

EDGES = Enum(
    value="EDGES",
    names=[("EAST", 0),
           ("NORTH_EAST", 1),
           ("NORTH", 2),
           ("WEST", 3),
           ("SOUTH_WEST", 4),
           ("SOUTH", 5)])
