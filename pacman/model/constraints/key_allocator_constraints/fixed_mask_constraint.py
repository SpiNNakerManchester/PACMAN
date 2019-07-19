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


class FixedMaskConstraint(AbstractKeyAllocatorConstraint):
    """ A key allocator that fixes the mask to be assigned to an edge.
    """

    __slots__ = [
        # the mask to be used during key allocation
        "_mask"
    ]

    def __init__(self, mask):
        """
        :param mask: the mask to be used during key allocation
        :type mask: int
        """
        self._mask = mask

    @property
    def mask(self):
        """ The mask to be used

        :return: The mask to be used
        :rtype: int
        """
        return self._mask

    def __eq__(self, other):
        if not isinstance(other, FixedMaskConstraint):
            return False
        return self._mask == other.mask

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._mask)

    def __repr__(self):
        return "FixedMaskConstraint(mask={})".format(self._mask)
