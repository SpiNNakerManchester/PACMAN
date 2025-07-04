# Copyright (c) 2017 The University of Manchester
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
from __future__ import annotations
from typing import (
    Collection, Dict, FrozenSet, Iterable, List, Mapping, Optional, Set, Tuple,
    Union, cast)


from typing_extensions import TypeAlias

from spinn_utilities.config_holder import get_config_bool
from spinn_utilities.timer import Timer

from spinn_machine import MulticastRoutingEntry, RoutingEntry

from pacman.exceptions import MinimisationFailedError
from pacman.utilities.constants import FULL_MASK
from pacman.model.routing_tables import UnCompressedMulticastRoutingTable
from pacman.operations.router_compressors import AbstractCompressor
from pacman.model.routing_tables import MulticastRoutingTables
from pacman.data.pacman_data_view import PacmanDataView

from .utils import intersect, remove_default_routes

#: A key,mask pair
_KeyMask: TypeAlias = Tuple[int, int]
#: A mapping from a key,mask pair to the things it aliases
_Aliases: TypeAlias = Dict[_KeyMask, FrozenSet[_KeyMask]]
#: A read-only mapping from a key,mask pair to the things it aliases
_ROAliases: TypeAlias = Mapping[_KeyMask, FrozenSet[_KeyMask]]
#: Sequence of all bit positions in a 32-bit word
_all_bits = tuple(1 << i for i in range(32))
# pylint: disable=wrong-spelling-in-comment


def ordered_covering_compressor() -> MulticastRoutingTables:
    """
    Compressor from rig that has been tied into the main tool chain stack.
    """
    compressor = _OrderedCoveringCompressor()
    return compressor.compress_all_tables()


class _OrderedCoveringCompressor(AbstractCompressor):
    """
    Compressor from rig that has been tied into the main tool chain stack.
    """
    __slots__ = ()

    def __init__(self) -> None:
        super().__init__(True)

    def compress_table(
            self, router_table: UnCompressedMulticastRoutingTable
            ) -> List[MulticastRoutingEntry]:
        """
        Reduce the size of a routing table by merging together entries where
        possible and by removing any remaining default routes.

        This is a wrapper around :py:func:`ordered_covering`.

        :param router_table:  Routing table to be merged.
        :return: The compressed table entries
        :raises MinimisationFailedError:
            If the smallest table that can be produced is larger than
            the space usually available in a hardware router table.
        """
        if get_config_bool(
                "Mapping", "router_table_compress_as_far_as_possible"):
            # Compress as much as possible
            target_length: Optional[int] = None
        else:
            chip = PacmanDataView.get_chip_at(router_table.x, router_table.y)
            target_length = chip.router.n_available_multicast_entries
        # Compress the router entries
        table, _ = ordered_covering(
            routing_table=router_table.multicast_routing_entries,
            target_length=target_length,
            aliases={}, no_raise=True, time_to_run_for=None)
        # Strip the defaultable routes
        return remove_default_routes(table, target_length)


def ordered_covering(
        routing_table: Iterable[MulticastRoutingEntry],
        target_length: Optional[int],
        aliases: _Aliases, *, no_raise: bool = False,
        time_to_run_for: Optional[float] = None
        ) -> Tuple[List[MulticastRoutingEntry], _Aliases]:
    """
    Reduce the size of a routing table by merging together entries where
    possible.

    .. warning::

        The input routing table *must* also include entries which could be
        removed and replaced by default routing.

    .. warning::

        It is assumed that the input routing table is not in any particular
        order and may be reordered into ascending order of generality (number
        of don't cares/*X*\\s in the key-mask) without affecting routing
        correctness.  It is also assumed that if this table is unordered it is
        at least orthogonal (i.e., there are no two entries which would match
        the same key) and reorderable.

    :param routing_table:
        Routing entries to be merged.
    :param target_length:
        Target length of the routing table; the minimisation procedure will
        halt once either this target is reached or no further minimisation is
        possible. If `None` then the table will be made as small as possible.
    :param aliases:
        Dictionary of which keys and masks in the routing table are
        combinations of other (now removed) keys and masks; this allows us to
        consider only the keys and masks the user actually cares about when
        determining if inserting a new entry will break the correctness of the
        table. This should be supplied when using this method to update an
        already minimised table, and should be an empty dictionary when
        compressing an uncompressed routing table.
    :param no_raise:
        If False (the default) then an error will be raised if the table cannot
        be minimised to be smaller than `target_length` and `target_length` is
        not `None`. If True then a table will be returned regardless of the
        size of the final table.
    :param time_to_run_for:
        If supplied, a maximum number of seconds to run for before giving an
        error. May only be obeyed approximately.
    :return: new routing table, A new _aliases dictionary.
    :raises MinimisationFailedError:
        If the smallest table that can be produced is larger than
        ``target_length``.
    """
    # Copy the aliases dictionary
    aliases = dict(aliases)

    timer = Timer()
    timer.start_timing()

    # Perform an initial sort of the routing table in order of increasing
    # generality.
    routing_table = sorted(routing_table, key=_get_entry_generality)

    while target_length is None or len(routing_table) > target_length:
        # Get the best merge
        merge = _get_best_merge(routing_table, aliases)

        # If there is no merge then stop
        if merge.goodness <= 0:
            break

        # Otherwise apply the merge; this returns a new routing table and
        # updates the aliases dictionary.
        routing_table = merge.apply(aliases)

        # control for limiting the search
        if time_to_run_for is not None:
            diff = timer.take_sample()
            if diff.total_seconds() >= time_to_run_for:
                raise MinimisationFailedError(
                    f"Best compression is {len(routing_table)} which is "
                    f"still higher than the target {target_length}")

    # If the table is still too big then raise an error
    if (not no_raise and target_length is not None and
            len(routing_table) > target_length):
        raise MinimisationFailedError(
            f"Best compression is {len(routing_table)} which is "
            f"still higher than the target {target_length}")

    # Return the finished routing table and aliases table
    return routing_table, aliases


def get_generality(key: int, mask: int) -> int:
    """
    Count the number of *X*\\s in the key-mask pair.

    For example, there are 32 *X*\\s in ``0x00000000/0x00000000``::

        >>> get_generality(0x0, 0x0)
        32

    And no *X*\\s in ``0xffffffff/0xffffffff``::

        >>> get_generality(0xffffffff, 0xffffffff)
        0

    :param key: Routing key
    :param mask: Routing mask
    """
    # 32-bit mask because Python uses infinite-precision ints
    xs = (~key) & (~mask) & 0xffffffff
    # See https://stackoverflow.com/a/9831671/301832
    # Can't use int.bit_count() until Python 10
    return bin(xs).count("1")


def _get_entry_generality(entry: Union[MulticastRoutingEntry, _Merge]) -> int:
    """
    Actually useful-in-this-file form of get_generality.
    """
    return get_generality(entry.key, entry.mask)


def _get_best_merge(
        routing_table: List[MulticastRoutingEntry],
        aliases: _ROAliases) -> '_Merge':
    """
    Inspect all possible merges for the routing table and return the merge
    which would combine the greatest number of entries.

    :param routing_table: Routing entries to be merged.
    :param aliases:
        Dictionary of which keys and masks in the routing table are
        combinations of other (now removed) keys and masks; this allows us to
        consider only the keys and masks the user actually cares about when
        determining if inserting a new entry will break the correctness of the
        table. This should be supplied when using this method to update an
        already minimised table.
    :return: Merge
    """
    # Create an empty merge to start with
    best_merge = _Merge(routing_table)
    best_goodness = 0

    # Look through every merge, discarding those that are no better than the
    # best we currently know about.
    for merge in _get_all_merges(routing_table):
        # If the merge isn't sufficiently good ignore it and move on
        if merge.goodness <= best_goodness:
            continue

        # After the merge refines itself to remove entries which would either
        # be aliased under other entries or entries which would cause the
        # aliasing of other entries we check if it is better than the current
        # best merge and reject it if it isn't.
        merge = _refine_merge(merge, aliases, min_goodness=best_goodness)
        if merge.goodness > best_goodness:
            # The merge we now have a reference to is better than the best
            # merge that we've previously encountered.
            best_merge = merge
            best_goodness = merge.goodness

    # Return the best merge and the best goodness for the calling method
    return best_merge


def _get_all_merges(routing_table: List[MulticastRoutingEntry]
                    ) -> Iterable['_Merge']:
    """
    Get possible sets of entries to merge.

    :param routing_table: Routing entries to be merged.
    """
    # Memorise entries that have been considered as part of a merge
    considered_entries: Set[int] = set()

    for i, entry in enumerate(routing_table):
        # If we've already considered this entry then skip
        if i in considered_entries:
            continue

        # Construct a merge by including other routing table entries below this
        # one which have equivalent routes.
        merge = {i}
        merge.update(
            j for j, other_entry in enumerate(routing_table[i+1:], start=i+1)
            if entry.spinnaker_route == other_entry.spinnaker_route)

        # Mark all these entries as considered
        considered_entries.update(merge)

        # If the merge contains multiple entries then yield it
        if len(merge) > 1:
            yield _Merge(routing_table, merge)


class _Merge(object):
    """
    Represents a potential merge of routing table entries.
    """

    _slots__ = [
        # Reference to the routing table against which the merge is defined.
        "routing_table",
        # Indices of entries in the routing table which are included in this
        # merge.
        "entries",
        # Key and mask pair generated by this merge.
        "key",
        "mask",
        # Number of ``X``s in the key - mask pair generated by this merge.
        "generality",
        # Measure of how "good" this merge is
        "goodness",
        # Where in the routing table the entry generated would need to be
        # inserted.
        "insertion_index",
        # Whether this merge is defaultable
        "defaultable"]

    def __init__(self, routing_table: List[MulticastRoutingEntry],
                 entries: Collection[int] = frozenset()):
        """
        :param routing_table:
        :param entries:
        """
        # Generate the new key, mask and sources
        any_ones = 0x00000000  # Wherever there is a 1 in *any* of the keys
        all_ones = FULL_MASK  # ... 1 in *all* of the keys
        all_selected = FULL_MASK  # ... 1 in *all* of the masks
        self.defaultable: bool = True

        for i in entries:
            # Get the entry
            entry = routing_table[i]

            # Update the values
            any_ones |= entry.key
            all_ones &= entry.key
            all_selected &= entry.mask
            self.defaultable &= entry.defaultable

        # Compute the goodness of the merge
        self.goodness: int = len(entries) - 1
        self.routing_table: List[MulticastRoutingEntry] = routing_table
        self.entries: FrozenSet[int] = frozenset(entries)

        # Compute the new mask, key and generality
        any_zeros = ~all_ones
        new_xs = any_ones ^ any_zeros
        self.mask: int = all_selected & new_xs  # Combine existing and new Xs
        self.key: int = all_ones & self.mask

        self.generality: int = _get_entry_generality(self)
        self.insertion_index = self._get_insertion_index()

    def _get_insertion_index(self) -> int:
        """
        Determine the index in the routing table where a new entry should be
        inserted if this merge is chosen.
        """
        # We insert before blocks of equivalent generality, so decrement the
        # starting generality.
        g = self.generality - 1

        # Perform a binary search through the routing table
        bottom = 0
        top = len(self.routing_table)
        pos = (top - bottom) // 2
        pg = _get_entry_generality(self.routing_table[pos])

        while pg != g and bottom < pos < top:
            if pg < g:
                bottom = pos  # Move up
            else:  # pg > generality
                top = pos  # Move down

            # Compute a new position
            pos = bottom + (top - bottom) // 2
            pg = _get_entry_generality(self.routing_table[pos])

        # Linear search up to find boundary to insert at
        while (pos < len(self.routing_table) and
               _get_entry_generality(self.routing_table[pos]) <= g):
            pos += 1

        return pos

    def apply(self, aliases: _Aliases) -> List[MulticastRoutingEntry]:
        """
        Apply the merge to the routing table it is defined against and get a
        new routing table.

        :param aliases:
            Dictionary of which keys and masks in the routing table are
            combinations of other (now removed) keys and masks; this allows us
            to consider only the keys and masks the user actually cares about
            when determining if inserting a new entry will break the
            correctness of the table. This should be supplied when using this
            method to update an already minimised table.
            *This dictionary will be updated by this method.*
        :return: new routing table
        """
        # Create a new routing table of the correct size
        new_size = len(self.routing_table) - len(self.entries) + 1
        new_table: List[Optional[MulticastRoutingEntry]] = [
            None for _ in range(new_size)]

        # Get the new entry
        routing_entry = RoutingEntry(
            spinnaker_route=self.routing_table[
                next(iter(self.entries))].spinnaker_route,
            defaultable=self.defaultable)
        new_entry = MulticastRoutingEntry(
            key=self.key, mask=self.mask, routing_entry=routing_entry)
        our_aliases: Set[_KeyMask] = set()

        # Iterate through the old table copying entries across
        insert = 0
        for i, entry in enumerate(self.routing_table):
            # If this is the insertion point then insert
            if i == self.insertion_index:
                new_table[insert] = new_entry
                insert += 1

            if i not in self.entries:
                # If this entry isn't to be removed then copy it across to the
                # new table.
                new_table[insert] = entry
                insert += 1
            else:
                # If this entry is to be removed then add it to the aliases
                # dictionary. It it already has aliases, merge those too
                km = (entry.key, entry.mask)
                our_aliases.update(aliases.pop(km, {km}))

        # Note the aliases we've just made
        aliases[self.key, self.mask] = frozenset(our_aliases)

        # If inserting beyond the end of the old table then insert at the end
        # of the new table.
        if self.insertion_index == len(self.routing_table):
            new_table[insert] = new_entry

        # All entries in new_table are now not None; cast is safe
        return cast(List[MulticastRoutingEntry], new_table)


def _refine_merge(
        merge: _Merge, aliases: _ROAliases, min_goodness: int) -> _Merge:
    """
    Remove entries from a merge to generate a valid merge which may be
    applied to the routing table.

    :param merge: Initial merge to refine.
    :param aliases:
        Dictionary of which keys and masks in the routing table are
        combinations of other (now removed) keys and masks; this allows us to
        consider only the keys and masks the user actually cares about when
        determining if inserting a new entry will break the correctness of the
        table. This should be supplied when using this method to update an
        already minimised table.
    :param min_goodness:
        Reject merges which are worse than the minimum goodness.
    :return: Valid merge which may be applied to the routing table
    """
    # Perform the down-check
    merge = _refine_downcheck(merge, aliases, min_goodness)

    # If the merge is still sufficiently good then continue to refine it.
    if merge.goodness > min_goodness:
        # Perform the up-check
        merge, changed = _refine_upcheck(merge, min_goodness)

        if changed and merge.goodness > min_goodness:
            # If the up-check removed any entries we need to re-perform the
            # down-check; but we do not need to re-perform the up-check as the
            # down check can only move the resultant merge nearer the top of
            # the routing table.
            merge = _refine_downcheck(merge, aliases, min_goodness)

    return merge


def _refine_upcheck(merge: _Merge, min_goodness: int) -> Tuple[_Merge, bool]:
    """
    Remove from the merge any entries which would be covered by entries
    between their current position and the merge insertion position.

    For example, the third entry of::

        0011 -> N
        0100 -> N
        1000 -> N
        X000 -> NE

    Cannot be merged with the first two entries because that would generate the
    new entry ``XXXX`` which would move ``1000`` below the entry with the
    key-mask pair of ``X000``, which would cover it.

    :return:
        New merge with entries possibly removed. If the goodness of the merge
        ever drops below `min_goodness` then an empty merge will be returned.
        (bool) If the merge has been changed at all
    """
    # Remove any entries which would be covered by entries above the merge
    # position.
    changed = False
    for i in sorted(merge.entries, reverse=True):
        # Get all the entries that are between the entry we're looking at the
        # insertion index of the proposed merged index. If this entry would be
        # covered up by any of them then we remove it from the merge.
        entry = merge.routing_table[i]
        key, mask = entry.key, entry.mask
        if any(intersect(key, mask, other.key, other.mask) for other in
               merge.routing_table[i+1:merge.insertion_index]):
            # The entry would be partially or wholly covered by another entry,
            # remove it from the merge and return a new merge.
            merge = _Merge(merge.routing_table, merge.entries - {i})
            changed = True

            # Check if the merge is sufficiently good
            if merge.goodness <= min_goodness:
                merge = _Merge(merge.routing_table)  # Replace with empty merge
                break

    # Return the final merge
    return merge, changed


def _refine_downcheck(
        merge: _Merge, aliases: _ROAliases, min_goodness: int) -> _Merge:
    """
    Prune the merge to avoid it covering up any entries which are below the
    merge insertion position.

    For example, in the (non-orthogonal) table::

        00001 -> N S
        00011 -> N S
        00100 -> N S
        00X00 -> N S
        XX1XX -> 3 5

    Merging the first four entries would generate the new key-mask ``00XXX``
    which would be inserted above the entry with the key-mask ``XX1XX``.
    However ``00XXX`` would stop the key ``00110`` from reaching its correct
    route, that is ``00110`` would be covered by ``00XXX``. To avoid this one
    could just abandon the merge entirely, but a better solution is to attempt
    to reduce the merge such that it no longer covers any entries below it.

    To do this we first identify the bits that ARE *X*\\s in the merged
    key-mask but which are NOT *X*\\s in the entry that we're covering. For
    this example this is the 3rd bit. We then look to remove from the merge any
    entries which are either *X*\\s in this position OR have the same value as
    in this bit as the aliased entry. As the 4th entry in the table has an
    *X* in this position we remove it, and as the 3rd entry has a *1* we
    also remove it.  For this example we would then consider merging only the
    first two entries, leading to a new key-mask pair of ``000X1`` which can be
    safely inserted between ``00X00`` and ``XX1XX``::

        00100 -> N S
        00X00 -> N S
        000X1 -> N S
        XX1XX -> 3 5

    :return:
        New merge with entries possibly removed. If the goodness of the merge
        ever drops below `min_goodness` then an empty merge will be returned.
    """
    # Operation
    # ---------
    # While the merge is still better than `min_goodness` we determine which
    # entries below it in the table it covers. For each of these covered
    # entries we find which bits are Xs in the merged entry and are NOT Xs in
    # the covered entry.
    #
    # For example:
    #
    #     Merged entry:      ...0XXX1...
    #     Covered entry:     ...010XX...
    #     Bits of interest:      ^^
    #     Label used below:      mn
    #
    # NOTE:
    #   The covered entry may be of lower generality than the prospective
    #   merged entry if it is contained within the aliases dictionary (e.g.,
    #   ...010XX... may be part of
    #   ``aliases = {...XXXXX...: {..., ...010XX..., ...}, ...})``
    #
    # In this case there are 2 bits of interest highlighted. These are bits in
    # the merge entry whose value can be set (by removing entries from the
    # merge) to avoid covering the covered entry. Whenever we have multiple
    # covered entries we care only about the entries with the fewest number of
    # ``settable`` bits because these most constrain which entries we may
    # remove from the merge to avoid covering up the lower entry.
    #
    # NOTE:
    #   * If there is only 1 ``settable`` bit then we are very constrained in
    #     terms of which entries must be removed from the merge to avoid
    #     covering a lower entry.
    #   * If there are no ``settable`` bits then we cannot possibly avoid
    #     covering the lower entry - the only correct action is to return an
    #     empty merge.
    #
    # Assuming that there were no covered entries without any ``settable`` bits
    # (that is ``stringency > 0``) then ``bits_and_vals`` contains pairs of
    # bits and boolean values which indicate which values need to be removed
    # from which bit positions to avoid covering up lower entries. If the
    # example above were the only covered entry then ``bits_and_vals`` would
    # contain ``(m, True)`` to indicate that all entries containing Xs or 1s in
    # the left-most bit of interest could be removed to avoid the covered entry
    # and ``(n, False)`` to indicate that all entries containing Xs or 0s in
    # the right-most bit of interest could be removed to avoid covering the
    # entry.
    #
    # NOTE:
    #   ``bits_and_vals`` consists of a set of options (e.g., we *could* remove
    #   all entries with Xs or 1s in bit ``m`` *or* we could remove all entries
    #   with Xs or 0s in bit ``n``, either would resolve the above covering).
    #
    # To determine which course of action to take we build a dictionary mapping
    # each of the pairs in ``bits_and_vals`` to the entries that would need to
    # be removed to "set" that bit in the merged entry. For example, we might
    # end up with:
    #
    #     options = {(m, True): {1, 4, 5},
    #                (n, False): {3, 7}}
    #
    # Indicating that we'd need to remove entries 1, 4 and 5 from the merge to
    # "set" the mth bit of the merged to 0 or that we'd need to remove entries
    # 3 and 7 to set the nth bit of the merged entry to set the nth bit to 1.
    #
    # NOTE:
    #   The boolean part of the pair indicates which value needs to be removed
    #   (True -> remove all 1s and Xs; False -> remove all 0s and Xs). If all
    #   Xs and 1s in a given bit position are removed from a merge then the
    #   merged entry is guaranteed to have a 0 in the bit position. Vice-versa
    #   removing all Xs and 0s in a given bit position from a merge will result
    #   in a merged entry with a 1 in that position.
    #
    # As we want to make our merges as large as possible we select the smallest
    # set of entries to remove from the merge from ``options``.
    #
    # The whole process is then repeated since:
    #   * we ignored covered entries with more ``settable`` bits there may
    #     still be covered entries below the merged entry
    #   * after removing entries from the merge the merged entry is of lower
    #     generality and is therefore nearer the top of the table so new
    #     entries may be have become covered

    # While the merge is still worth considering continue to perform the
    # down-check.
    while merge.goodness > min_goodness:
        covered = _get_covered_keys_and_masks(merge, aliases)

        # For each covered entry work out which bits in the key-mask pair which
        # are not Xs are not covered by Xs in the merge key-mask pair. Only
        # keep track of the entries which have the fewest bits that we could
        # set.
        most_stringent = 33  # Not at all stringent
        bits_and_vals: Set[Tuple[int, int]] = set()
        for key, mask in covered:
            # Get the bit positions where there ISN'T an X in the covered entry
            # but there IS an X in the merged entry.
            settable = mask & ~merge.mask

            # Count the number of settable bits, if this is a more stringent
            # constraint than the previous constraint then ensure that we
            # record the new stringency and store which bits we need to set to
            # meet the constraint.
            n_settable = sum(1 for bit in _all_bits if bit & settable)
            # TODO: use int.bit_count() for above once 3.10 is min Py ver
            if n_settable <= most_stringent:
                if n_settable < most_stringent:
                    most_stringent = n_settable
                    bits_and_vals = set()

                # Add this settable mask and the required values to the
                # settables list.
                bits_and_vals.update(
                    (bit, not (key & bit))
                    for bit in _all_bits if bit & settable)

        if most_stringent == 33:
            # If the stringency is at default, there are no covered entries
            # (the merge is valid) then break out of the loop.
            break
        if most_stringent == 0:
            # If are there any instances where we could not possibly change a
            # bit to avoid aliasing an entry we'll return an empty merge and
            # give up.
            merge = _Merge(merge.routing_table)
            break

        # Get the smallest number of entries to remove to modify the
        # resultant key-mask to avoid covering a lower entry. Prefer to
        # modify more significant bits of the key mask.
        remove: Set[int] = set()  # Entries to remove
        for bit, val in sorted(bits_and_vals, reverse=True):
            working_remove: Set[int] = set()  # Holder for working remove set

            for i in merge.entries:
                entry = merge.routing_table[i]
                if (not entry.mask & bit) or (
                        bool(entry.key & bit) is (not val)):
                    # If the entry has an X in this position then it will
                    # need to be removed regardless of whether we want to
                    # set a 0 or a 1 in this position, likewise it will
                    # need to be removed if it is a 0 and we want a 1 or
                    # vice-versa.
                    working_remove.add(i)

            # If the current remove set is empty or the new remove set is
            # smaller update the remove set.
            if not remove or len(working_remove) < len(remove):
                remove = working_remove

            # Remove the selected entries from the merge
            merge = _Merge(merge.routing_table, merge.entries - remove)
    else:
        # NOTE: If there are no covered entries, that is, if the merge is
        # better than min goodness AND valid this `else` clause is not reached.
        # Ensure than an empty merge is returned if the above loop was aborted
        # early with a non-empty merge.
        merge = _Merge(merge.routing_table)

    return merge


def _get_covered_keys_and_masks(
        merge: _Merge, aliases: _ROAliases) -> List[_KeyMask]:
    """
    Get keys and masks which would be covered by the entry resulting from
    the merge.

    :param merge:
    :param aliases: {(key, mask): {(key, mask), ...}, ...}
        Map of key-mask pairs to the sets of key-mask pairs that they actually
        represent.
    :return: (key, mask)
        Pairs of keys and masks which would be covered if the given `merge`
        were to be applied to the routing table.
    """
    # For every entry in the table below the insertion index see which keys
    # and masks would overlap with the key and mask of the merged entry.
    covered: List[_KeyMask] = list()
    for entry in merge.routing_table[merge.insertion_index:]:
        km = (entry.key, entry.mask)
        for key_mask in aliases.get(km, {km}):
            key, mask = key_mask
            if intersect(merge.key, merge.mask, key, mask):
                covered.append(key_mask)
    return covered
