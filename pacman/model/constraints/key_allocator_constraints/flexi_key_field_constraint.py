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


class FlexiKeyFieldConstraint(AbstractKeyAllocatorConstraint):
    """ Constraint that indicates fields in the mask without a specific size\
        or position.
    """

    __slots__ = [
        # any fields that define regions in the mask with further limitations
        "_fields"
    ]

    def __init__(self, fields):
        self._fields = fields

    @property
    def fields(self):
        return self._fields

    def __eq__(self, other):
        if not isinstance(other, FlexiKeyFieldConstraint):
            return False
        if len(self._fields) != len(other.fields):
            return False
        return all(field in other.fields for field in self._fields)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(frozenset(self._fields))

    def __repr__(self):
        return "FlexiKeyFieldConstraint(fields={})".format(
            self._fields)
