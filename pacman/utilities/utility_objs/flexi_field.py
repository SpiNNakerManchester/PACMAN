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


class SUPPORTED_TAGS(Enum):
    APPLICATION = 0
    ROUTING = 1


class FlexiField(object):
    """ Field who's location is not fixed in key allocation
    """

    __slots__ = [
        # identifier
        "_flexi_field_name",

        # what value to store in this field
        "_value",

        # the tag
        "_tag",

        # the number of keys to store within this field
        "_instance_n_keys",

        # how deep in recursive fields this field resides.
        "_nested_level"
    ]

    def __init__(
            self, flexi_field_name, value=None, instance_n_keys=None, tag=None,
            nested_level=0):
        # pylint: disable=too-many-arguments
        self._flexi_field_name = flexi_field_name
        self._value = value
        self._tag = tag
        self._instance_n_keys = instance_n_keys
        self._nested_level = nested_level

    @property
    def name(self):
        """ The name for this Flexible field
        """
        return self._flexi_field_name

    @property
    def value(self):
        return self._value

    @property
    def tag(self):
        return self._tag

    @property
    def instance_n_keys(self):
        return self._instance_n_keys

    def __eq__(self, other):
        if not isinstance(other, FlexiField):
            return False
        return (self._flexi_field_name == other.name and
                self._instance_n_keys == other.instance_n_keys and
                self._tag == other.tag)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        if self._instance_n_keys is not None:
            return (self._flexi_field_name, self._instance_n_keys,
                    self._tag).__hash__()
        return (self._flexi_field_name, self._value,
                self._tag).__hash__()

    def __repr__(self):
        return "ID:{}:IV:{}:INK:{}:TAG:{}".format(
            self._flexi_field_name, self._value, self._instance_n_keys,
            self._tag)
