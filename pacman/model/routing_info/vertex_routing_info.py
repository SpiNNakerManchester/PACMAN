# Copyright (c) 2021 The University of Manchester
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
from spinn_utilities.abstract_base import abstractproperty, AbstractBase


class VertexRoutingInfo(object, metaclass=AbstractBase):
    """ Associates a partition identifier to its routing information
        (keys and masks).
    """

    __slots__ = [
        # The keys allocated to the machine partition
        "__keys_and_masks",

        # The partition identifier of the allocation
        "__partition_id"
    ]

    def __init__(self, keys_and_masks, partition_id):
        """
        :param iterable(BaseKeyAndMask) keys_and_masks:\
            The keys allocated to the machine partition
        :param str partition_id: The partition to set the keys for
        :param MachineVertex machine_vertex: The vertex to set the keys for
        :param int index: The index of the machine vertex
        """
        self.__keys_and_masks = keys_and_masks
        self.__partition_id = partition_id

    def get_keys(self, n_keys=None):
        """ Get the ordered list of individual keys allocated to the edge

        :param int n_keys: Optional limit on the number of keys to return
        :return: An array of keys
        :rtype: ~numpy.ndarray
        """

        max_n_keys = sum(km.n_keys for km in self.__keys_and_masks)

        if n_keys is None:
            n_keys = max_n_keys
        elif max_n_keys < n_keys:
            raise PacmanConfigurationException(
                "You asked for {} keys, but the routing info can only "
                "provide {} keys.".format(n_keys, max_n_keys))

        key_array = numpy.zeros(n_keys, dtype=">u4")
        offset = 0
        for key_and_mask in self.__keys_and_masks:
            _, offset = key_and_mask.get_keys(
                key_array=key_array, offset=offset, n_keys=(n_keys - offset))
        return key_array

    @property
    def keys_and_masks(self):
        """
        :rtype: iterable(BaseKeyAndMask)
        """
        return self.__keys_and_masks

    @property
    def first_key_and_mask(self):
        """ The first key and mask (or only one if there is only one)

        :rtype: BaseKeyAndMask
        """
        return self.__keys_and_masks[0]

    @property
    def first_key(self):
        """ The first key (or only one if there is only one)

        :rtype: int
        """
        return self.__keys_and_masks[0].key

    @property
    def first_mask(self):
        """ The first mask (or only one if there is only one)

        :rtype: int
        """
        return self.__keys_and_masks[0].mask

    @property
    def partition_id(self):
        """ The identifier of the partition

        :rtype: str
        """
        return self.__partition_id

    @abstractproperty
    def vertex(self):
        """ The vertex of the information

        :rtype: ApplicationVertex or MachineVertex
        """
