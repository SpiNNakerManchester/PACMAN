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

import pytest
from pacman.operations.routing_info_allocator_algorithms.\
    malloc_based_routing_allocator.utils import (
        get_possible_masks)


def test_mask_generator():
    """ This checks behaviour, but with restricted bitfield sizes.
    """
    assert frozenset(get_possible_masks(2, 4, False)) == frozenset(
        {14, 13, 11, 7})
    assert frozenset(get_possible_masks(2, 4, True)) == frozenset(
        {14})
    assert frozenset(get_possible_masks(5, 4, False)) == frozenset(
        {1, 2, 4, 8})
    assert frozenset(get_possible_masks(5, 5, False)) == frozenset(
        {3, 5, 6, 9, 10, 12, 17, 18, 20, 24})
    assert frozenset(get_possible_masks(7, 5, False)) == frozenset(
        {3, 5, 6, 9, 10, 12, 17, 18, 20, 24})
    assert frozenset(get_possible_masks(7, 3, False)) == frozenset(
        {0})
    with pytest.raises(AssertionError):
        # Can't fit
        get_possible_masks(7, 2, False)
