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

from enum import Enum
import uuid


class SUPPORTED_TAGS(Enum):
    APPLICATION = 0
    ROUTING = 1


class Field(object):
    """ Field object used in a field constraint for key allocation
    """

    __slots__ = [
        "_lo",
        "_hi",
        "_value",
        "_tag",
        "_name"
    ]

    def __init__(self, lo, hi, value, tag=SUPPORTED_TAGS.ROUTING, name=None):
        """
        :param int lo: the low bit in the routing table entry for this field
        :param int hi: the high bit in the routing table entry for this field
        :param int value: the value to store in this field
        :param SUPPORTED_TAGS tag: field tag
        :param name: field name
        :type name: str or None
        """
        # pylint: disable=too-many-arguments
        self._lo = lo
        self._hi = hi
        self._value = value
        self._tag = tag
        self._name = uuid.uuid4() if name is None else name

    @property
    def lo(self):
        """ the low bit in the routing table entry for this field

        :rtype: int
        """
        return self._lo

    @property
    def hi(self):
        """ the high bit in the routing table entry for this field

        :rtype: int
        """
        return self._hi

    @property
    def name(self):
        """ field name

        :rtype: str or ~uuid.UUID
        """
        return self._name

    @name.setter
    def name(self, new_value):
        self._name = new_value

    @property
    def value(self):
        """ the value to store in this field

        :rtype: int
        """
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value

    @property
    def tag(self):
        """ field tag

        :rtype: SUPPORTED_TAGS
        """
        return self._tag

    @tag.setter
    def tag(self, new_value):
        self._tag = new_value

    def __repr__(self):
        return "Field(lo={}, hi={}, value={}, tag={}, name={})".format(
            self.lo, self.hi, self.value, self._value, self._name)

    def __str__(self):
        return self.__repr__()

    def __hash__(self):
        return (self._lo, self._hi, self._value, self._tag,
                self._name).__hash__()

    def __eq__(self, other_field):
        if not isinstance(other_field, Field):
            return False
        return (
            self._lo == other_field.lo and self._hi == other_field.hi and
            self._value == other_field.value and
            self._tag == other_field.tag and
            self._name == other_field.name)

    def __ne__(self, other):
        return not self.__eq__(other)
