# Copyright (c) 2016 The University of Manchester
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
