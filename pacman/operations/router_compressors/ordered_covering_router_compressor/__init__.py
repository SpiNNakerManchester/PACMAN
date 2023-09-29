# Copyright (c) 2015 The University of Manchester
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
"""
Ordered Covering
================

An novel algorithm for the minimisation of SpiNNaker's multicast routing tables
devised by Andrew Mundy.

Background
----------

SpiNNaker routing tables consist of entries made up of a 32-bit key, a 32-bit
mask and a 24-bit route value. The key and mask of every entry act as a sieve
for the keys found on incoming multicast packets. Each bit of the key-mask pair
can be considered as matching 0, 1 or 2 values in the same bit of a multicast
packet key:

 =====   =====   ==================   =======
 Key     Mask    Matches Key Values   Written
 =====   =====   ==================   =======
 ``0``   ``0``   ``0`` or ``1``       ``X``
 ``0``   ``1``   ``0``                ``0``
 ``1``   ``1``   ``1``                ``1``
 ``1``   ``0``   Nothing              ``!``
 =====   =====   ==================   =======

If a packet matches the key-mask of an entry then the packet is transmitted to
the cores and links indicated by the route field.

For example, if the table were:

 ========  ========  =================
 Key       Mask      Route
 ========  ========  =================
 ``0000``  ``1111``  North, North East
 ``0111``  ``0111``  South
 ========  ========  =================

Which, from now on, will be written as::

    0000 -> N NE
    X111 -> S

Then any packets with the key ``0000`` would be sent out of the north and
north-east links. Any packets with the keys ``0111`` or ``1111`` would be sent
out of the south link only.

Entries in table are ordered, with entries at the top of the table having
higher priority than those lower down the table. Only the highest priority
entry which matches a packet is used. If, for example, the table were::

    0000 -> N NE
    1111 -> 1 2
    X111 -> S

Then packets with the keys ``0000`` and ``0111`` would be treated as before.
However, packets with the key ``1111`` would be sent to cores 1 and 2 as only
the higher priority entry has effect.

Merging routing table entries
-----------------------------

Routing tables can be minimised by merging together entries with equivalent
routes. This is done by creating a new key-mask pair with an ``X`` wherever the
key-mask pairs of any of the original entries differed.

For example, merging of the entries::

    0000 -> N
    0001 -> N

Would lead to the new entry:

    000X -> N

Which would match any of the keys matched by the original entries but no more.
In contrast the merge of ``0001`` and ``0010`` would generate the new entry
``00XX`` which would match keys matched by either of the original entries but
also ``0000`` and ``0011``.

Clearly, if we are to attempt to minimise tables such as::

    0001 -> N
    0010 -> N
    0000 -> S, SE
    0011 -> SE

We need a set of rules for:

 1. Where merged entries are to be inserted into the table
 2. Which merges are allowed

"Ordered Covering"
------------------

The algorithm implemented here, "Ordered Covering", provides the following
rule:

 * The only merges allowed are those which:

   a) would not cause one of the entries in the merge to be "hidden" below
      an entry of lesser generality than the merged entry but which matched
      any of the same keys. For example, merging ``0010`` and ``0001`` would
      not be allowed if the new entry would be placed below the existing
      entry ``000X`` as this would "hide" ``0001``.
   b) would not cause an entry "contained" within an entry of higher
      generality to be hidden by the insertion of a new entry. For example, if
      the entry ``XXXX`` had been formed by merging the entries ``0011`` and
      ``1100`` then merging of the entries ``1101`` and ``1110`` would not be
      allowed as it would cause the entry ``11XX`` to be inserted above
      ``XXXX`` in the table and would hide ``1100``.

Following these rules ensures that the minimised table will be functionally
equivalent to the original table provided that the original table was invariant
under reordering OR was provided in increasing order of generality.

As a heuristic:

 * Routing tables are to be kept sorted in increasing order of "generality",
   that is the number of ``X``s in the entry. An entry with the key-mask pair
   ``00XX`` must be placed below any entries with fewer ``X``s in their
   key-mask pairs (e.g., below ``0000`` and ``000X``).

   a) New entries must also be inserted below any entries of the same
      generality. If ``XX00`` were already present in the table the new entry
      ``0XX0`` must be inserted below it.

based on
https://github.com/project-rig/rig/blob/master/rig/routing_table/ordered_covering.py

Implementation API
==================
"""
from .ordered_covering import get_generality, minimise, ordered_covering
from .remove_default_routes import remove_default_routes
from .ordered_covering_compressor import ordered_covering_compressor
from .utils import intersect

__all__ = (
    "get_generality",
    "intersect",
    "minimise",
    "ordered_covering",
    "ordered_covering_compressor",
    "remove_default_routes"
    )
