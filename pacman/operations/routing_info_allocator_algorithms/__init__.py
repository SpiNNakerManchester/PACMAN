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

from .basic_routing_info_allocator import BasicRoutingInfoAllocator
from .destination_based_key_allocator import (
    DestinationBasedRoutingInfoAllocator)
from .zoned_routing_info_allocator import (
    ZonedRoutingInfoAllocator)
from pacman.operations.routing_info_allocator_algorithms.\
    malloc_based_routing_allocator.malloc_based_routing_info_allocator \
    import (
        MallocBasedRoutingInfoAllocator)
from pacman.operations.routing_info_allocator_algorithms.\
    malloc_based_routing_allocator.\
    compressible_malloc_based_routing_info_allocator import (
        CompressibleMallocBasedRoutingInfoAllocator)

__all__ = ['BasicRoutingInfoAllocator',
           'CompressibleMallocBasedRoutingInfoAllocator',
           'DestinationBasedRoutingInfoAllocator',
           'MallocBasedRoutingInfoAllocator',
           'ZonedRoutingInfoAllocator']
