import random
import pytest

from pacman.operations.router_compressors.\
    mundys_router_compressor.routing_table_condenser import \
    MundyRouterCompressor

from pacman import exceptions


def test_create_mask():
    crusher = MundyRouterCompressor()
    assert crusher.create_mask(0, 0) == ~0x1
    assert crusher.create_mask(1, 0) == ~0x3
    assert crusher.create_mask(2, 0) == ~0x7
    assert crusher.create_mask(2, 1) == ~0x6
    assert crusher.create_mask(2, 2) == ~0x4


def test_generate_increasing_lsb_masks():
    for _ in range(1000):
        msb = random.randint(0, 31)
        lsb = random.randint(0, msb)
        crusher = MundyRouterCompressor()
        base_mask = crusher.create_mask(msb, lsb)

        for (i, m) in enumerate(
                crusher.generate_increasing_lsb_masks(msb, lsb)):
            n = (2**(i) - 1) << lsb
            assert m == base_mask | n


def test_generate_decreasing_msb_masks():
    for _ in range(1000):
        msb = random.randint(0, 31)
        lsb = random.randint(0, msb)
        crusher = MundyRouterCompressor()
        base_mask = crusher.create_mask(msb, lsb)

        for (i, m) in enumerate(
                crusher.generate_decreasing_msb_masks(msb, lsb)):
            n = (2**(i) - 1) << (msb + 1 - i)
            assert m == base_mask | n
            print "0x%08x" % m


def test_get_matching_entries():
    crusher = MundyRouterCompressor()
    entries = [
        crusher.RoutingEntry(0xff000000, 0xff000000, 1, False),
        crusher.RoutingEntry(0xfa000000, 0xff000000, 1, False),
        crusher.RoutingEntry(0x00ff0000, 0x00ff0000, 2, False),
        crusher.RoutingEntry(0xfb000000, 0xff000000, 2, False),
    ]

    matches = crusher.get_matching_entries(0xfa000000, 0xfa000000, entries)
    assert entries[0] in matches
    assert entries[1] in matches
    assert entries[3] in matches
    assert entries[2] not in matches


def test_get_possible_nonordered_merges_no_merges():
    crusher = MundyRouterCompressor()
    entries = [
        crusher.RoutingEntry(0xf1, 0xff, 1, False),
        crusher.RoutingEntry(0xf2, 0xff, 2, False),
    ]

    matches = crusher.get_possible_nonordered_merges(0xf0, entries)
    assert len(matches) == 0


def test_get_possible_nonordered_merges_merges():
    crusher = MundyRouterCompressor()
    entries = [
        crusher.RoutingEntry(0xf0, 0xff, 1, False),
        crusher.RoutingEntry(0xf1, 0xff, 1, False),
        crusher.RoutingEntry(0xf2, 0xff, 2, False),
    ]

    matches = crusher.get_possible_nonordered_merges(0xfe, entries)
    k0 = crusher.KeyMask(0xf0, 0xfe)
    k1 = crusher.KeyMask(0xf1, 0xfe)
    k2 = crusher.KeyMask(0xf2, 0xfe)

    assert len(matches) == 2
    assert k0 in matches and k2 in matches
    assert k1 not in matches

    assert entries[0] in matches[k0]
    assert entries[1] in matches[k0]
    assert len(matches[k0]) == 2

    assert entries[2] in matches[k2]
    assert len(matches[k2]) == 1


def test_get_possible_nonordered_merges_merges2():
    crusher = MundyRouterCompressor()
    entries = [
        crusher.RoutingEntry(0xf0, 0xff, 1, False),
        crusher.RoutingEntry(0xf4, 0xff, 1, False),
        crusher.RoutingEntry(0xf5, 0xff, 1, False),
        crusher.RoutingEntry(0xf1, 0xff, 1, False),
        crusher.RoutingEntry(0xf2, 0xff, 2, False),
    ]

    matches = crusher.get_possible_nonordered_merges(0xfc, entries)
    k0 = crusher.KeyMask(0xf0, 0xfc)
    k1 = crusher.KeyMask(0xf4, 0xfc)

    assert len(matches) == 1
    assert k0 not in matches and k1 in matches

    assert len(matches[k1]) == 2
    assert entries[1] in matches[k1]
    assert entries[2] in matches[k1]


def test_get_best_nonordered_merge_no_merges():
    # There is no possible merge within this set, assert that an appropriate
    # exception is raised.
    crusher = MundyRouterCompressor()
    entries = [
        crusher.RoutingEntry(0xf1, 0xff, 1, False),
        crusher.RoutingEntry(0xf2, 0xff, 2, False),
    ]

    with pytest.raises(exceptions.PacmanNoMergeException):
        crusher.get_best_nonordered_merge(0xf0, entries, None)


def test_get_best_nonordered_merge_only_default():
    # There is no point in turning a defaultable entry into an entry in the
    # table, and there are no other merges. Ensure an appropriate exception is
    # raised.
    crusher = MundyRouterCompressor()
    entries = [
        crusher.RoutingEntry(0xf1, 0xff, 1, True),
    ]

    with pytest.raises(exceptions.PacmanNoMergeException):
        crusher.get_best_nonordered_merge(0xf0, entries, None)

def test_get_best_nonordered_merge():
    # Ensure we get the best merge returned.
    crusher = MundyRouterCompressor()
    entries = [
        crusher.RoutingEntry(0xf8, 0xff, 1, False),
        crusher.RoutingEntry(0xf4, 0xff, 1, False),
        crusher.RoutingEntry(0xf3, 0xff, 2, False),
        crusher.RoutingEntry(0xf1, 0xff, 2, False),
        crusher.RoutingEntry(0xf2, 0xff, 2, False),
    ]
    km, old, new = crusher.get_best_nonordered_merge(
        0xfc, entries, crusher.RoutingEntry)

    # The best merge should be that with route == 2
    assert km.key == 0xf0
    assert km.mask == 0xfc

    assert entries[2] in old
    assert entries[3] in old
    assert entries[4] in old

    assert len(new) == 1
    assert new[0].route == 2


def test_reduce_routing_table_too_small():
    # If there are fewer than n entries the reduction shouldn't bother trying
    # to anything.
    crusher = MundyRouterCompressor()
    entries = [
        crusher.RoutingEntry(0xf8, 0xff, 1, False),
        crusher.RoutingEntry(0xf4, 0xff, 1, False),
        crusher.RoutingEntry(0xf3, 0xff, 2, False),
        crusher.RoutingEntry(0xf1, 0xff, 2, False),
        crusher.RoutingEntry(0xf2, 0xff, 2, False),
    ]
    new_entries = crusher.reduce_routing_table(entries, [(7,2)])
    assert new_entries == entries


def test_reduce_routing_table_simple():
    # Test that only one merge is made, and that it is made correctly
    crusher = MundyRouterCompressor()
    entries = [
        crusher.RoutingEntry(0xf8, 0xff, 1, False),
        crusher.RoutingEntry(0xf4, 0xff, 1, False),
        crusher.RoutingEntry(0xf3, 0xff, 2, False),
        crusher.RoutingEntry(0xf1, 0xff, 2, False),
        crusher.RoutingEntry(0xf2, 0xff, 2, False),
    ]
    new_entries = crusher.reduce_routing_table(entries, [(1, 0)],
                                               max_entries=4)

    assert len(new_entries) == 3
    assert new_entries[0:1] == entries[0:1]
    assert new_entries[-1] == crusher.RoutingEntry(0xf0, 0xfc, 2, False)
    assert crusher.get_routed_entries(0xf3, new_entries) == [new_entries[2]]
    assert crusher.get_routed_entries(0xf1, new_entries) == [new_entries[2]]
    assert crusher.get_routed_entries(0xf2, new_entries) == [new_entries[2]]
    assert crusher.get_routed_entries(0xf8, new_entries) == [new_entries[0]]
    assert crusher.get_routed_entries(0xf4, new_entries) == [new_entries[1]]
