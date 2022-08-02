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

from pacman.model.constraints import AbstractConstraint
from pacman.model.routing_info import BaseKeyAndMask
from pacman.exceptions import PacmanConfigurationException


class FixedKeyAndMaskConstraint(AbstractConstraint):
    """ Key allocator constraint that fixes the key and mask of an edge.

    .. note::
        Used for neuron-connected input ("sensory neurons") and output
        ("motor neurons") devices.
    """

    __slots__ = [
        # The key and mask combinations to fix
        "_keys_and_masks",

        # The identifier of the partition to which this applies, or None
        # if only one partition is expected
        "_partition"

    ]

    def __init__(self, keys_and_masks, partition=None):
        """
        :param iterable(BaseKeyAndMask) keys_and_masks:
            The key and mask combinations to fix
        :param partition:
            The identifier of the partition to which this constraint applies,
            or None if it applies to all partitions (meaning there is only
            one partition expected)
        :type partition: str or None
        """
        for keys_and_mask in keys_and_masks:
            if not isinstance(keys_and_mask, BaseKeyAndMask):
                raise PacmanConfigurationException(
                    "the keys and masks object contains a object that is not"
                    "a key_and_mask object")

        self._keys_and_masks = keys_and_masks
        self._partition = partition

    @property
    def keys_and_masks(self):
        """ The keys and masks to be fixed

        :return: An iterable of key and mask combinations
        :rtype: iterable(BaseKeyAndMask)
        """
        return self._keys_and_masks

    @property
    def partition(self):
        """ The identifier of the partition to which this constraint applies,
            or None if it applies to the only expected partition

        :rtype: str or None
        """
        return self._partition

    def applies_to_partition(self, partition):
        """ Determine if this applies to the given partition identifier or not

        :param str partition: The identifier of the partition to check
        :rtype: bool
        """
        return self._partition is None or self._partition == partition

    def __repr__(self):
        return (
            "FixedKeyAndMaskConstraint("
            "keys_and_masks={}, partition={})".format(
                self._keys_and_masks, self._partition))

    def __eq__(self, other):
        if not isinstance(other, FixedKeyAndMaskConstraint):
            return False
        if len(self._keys_and_masks) != len(other.keys_and_masks):
            return False
        return all(km in other.keys_and_masks for km in self._keys_and_masks)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return frozenset(self._keys_and_masks).__hash__()
