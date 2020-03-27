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

from .abstract_key_allocator_constraint import AbstractKeyAllocatorConstraint


class ContiguousKeyRangeContraint(AbstractKeyAllocatorConstraint):
    """ Key allocator constraint that keeps the keys allocated to a contiguous
    range.  Without this constraint, keys can be allocated across the key
    space.

    .. note::
        All current key allocators *always* allocate contiguous keys.
    """

    __slots__ = []

    def __eq__(self, other):
        return isinstance(other, ContiguousKeyRangeContraint)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash("ContiguousKeyRangeContraint")

    def __repr__(self):
        return "KeyAllocatorContiguousRangeConstraint()"
