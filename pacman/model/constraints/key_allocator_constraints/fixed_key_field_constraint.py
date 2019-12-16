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


class FixedKeyFieldConstraint(AbstractKeyAllocatorConstraint):
    """ Constraint that indicates fields in the mask of a key.
    """

    __slots__ = [
        # any fields that define regions in the mask with further limitations
        "_fields"
    ]

    def __init__(self, fields):
        """
        :param iterable(Field) fields:
            any fields that define regions in the mask with further limitations
        :raise PacmanInvalidParameterException:
            if any of the fields are outside of the mask i.e.,:

                mask & field.value != field.value

            or if any of the field masks overlap i.e.,:

                field.value & other_field.value != 0
        """
        self._fields = sorted(fields, key=lambda field: field.value,
                              reverse=True)
        # TODO: Enforce the documented restrictions

    @property
    def fields(self):
        """ Any fields in the mask, i.e., ranges of the mask that have\
            further limitations

        :return: Iterable of fields, ordered by mask with the highest bit\
            range first
        :rtype: list(Field)
        """
        return self._fields

    def __eq__(self, other):
        if not isinstance(other, FixedKeyFieldConstraint):
            return False
        if len(self._fields) != len(other.fields):
            return False
        return all(field in other.fields for field in self._fields)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        frozen_fields = frozenset(self._fields)
        return hash(frozen_fields)

    def __repr__(self):
        return "FixedKeyFieldConstraint(fields={})".format(
            self._fields)
