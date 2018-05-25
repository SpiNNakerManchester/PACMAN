import pytest
from pacman.operations.routing_info_allocator_algorithms.\
    malloc_based_routing_allocator.utils import (
        get_possible_masks)


def test_mask_generator():
    """ This checks behaviour, but with restricted bitfield sizes.
    """
    assert frozenset(get_possible_masks(2, 4)) == frozenset(
        {14, 13, 11, 7})
    assert frozenset(get_possible_masks(5, 4)) == frozenset(
        {1, 2, 4, 8})
    assert frozenset(get_possible_masks(5, 5)) == frozenset(
        {3, 5, 6, 9, 10, 12, 17, 18, 20, 24})
    assert frozenset(get_possible_masks(7, 5)) == frozenset(
        {3, 5, 6, 9, 10, 12, 17, 18, 20, 24})
    assert frozenset(get_possible_masks(7, 3)) == frozenset(
        {0})
    with pytest.raises(AssertionError):
        # Can't fit
        get_possible_masks(7, 2)
