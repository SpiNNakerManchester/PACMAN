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

import numpy
from pacman.exceptions import PacmanConfigurationException


class PartitionRoutingInfo(object):
    """ Associates a partition to its routing information (keys and masks).
    """

    __slots__ = [
        # The keys allocated to the machine partition
        "_keys_and_masks",

        # The partition to set the number of keys for
        "_partition"
    ]

    def __init__(self, keys_and_masks, partition):
        """
        :param iterable(BaseKeyAndMask) keys_and_masks:\
            The keys allocated to the machine partition
        :param AbstractSingleSourcePartition partition:\
            The partition to set the number of keys for
        """
        self._keys_and_masks = keys_and_masks
        self._partition = partition

    def get_keys(self, n_keys=None):
        """ Get the ordered list of individual keys allocated to the edge

        :param int n_keys: Optional limit on the number of keys to return
        :return: An array of keys
        :rtype: ~numpy.ndarray
        """

        max_n_keys = sum(km.n_keys for km in self._keys_and_masks)

        if n_keys is None:
            n_keys = max_n_keys
        elif max_n_keys < n_keys:
            raise PacmanConfigurationException(
                "You asked for {} keys, but the routing info can only "
                "provide {} keys.".format(n_keys, max_n_keys))

        key_array = numpy.zeros(n_keys, dtype=">u4")
        offset = 0
        for key_and_mask in self._keys_and_masks:
            _, offset = key_and_mask.get_keys(
                key_array=key_array, offset=offset, n_keys=(n_keys - offset))
        return key_array

    @property
    def keys_and_masks(self):
        """
        :rtype: iterable(BaseKeyAndMask)
        """
        return self._keys_and_masks

    @property
    def first_key_and_mask(self):
        """ The first key and mask (or only one if there is only one)

        :rtype: BaseKeyAndMask
        """
        return self._keys_and_masks[0]

    @property
    def first_key(self):
        """ The first key (or only one if there is only one)

        :rtype: int
        """
        return self._keys_and_masks[0].key

    @property
    def first_mask(self):
        """ The first mask (or only one if there is only one)

        :rtype: int
        """
        return self._keys_and_masks[0].mask

    @property
    def partition(self):
        """
        :rtype: AbstractSingleSourcePartition
        """
        return self._partition

    def __repr__(self):
        return "partition:{}, keys_and_masks:{}".format(
            self._partition, self._keys_and_masks)
