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
from pacman.exceptions import PacmanNotExistException
from spinn_utilities.overrides import overrides
from .abstract_machine_partition_n_keys_map import (
    AbstractMachinePartitionNKeysMap)


class DictBasedMachinePartitionNKeysMap(AbstractMachinePartitionNKeysMap):
    """ A python dict-based implementation of the\
        :py:class:`AbstractMachinePartitionNKeysMap`
    """

    NOT_EXIST_ERROR_MESSAGE = (
        "Partition {} does not exist in the mapping to n keys")

    __slots__ = [
        # A mapping of [partition] -> number of keys to use via this partition
        "_n_keys_map"
    ]

    def __init__(self):
        self._n_keys_map = dict()

    def set_n_keys_for_partition(self, partition, n_keys):
        """ Set the number of keys required by a machine outgoing edge\
            partition

        :param AbstractSingleSourcePartition partition:
            The partition to set the number of keys for
        :param int n_keys: The number of keys required by the edge
        """
        self._n_keys_map[partition] = int(n_keys)

    @overrides(AbstractMachinePartitionNKeysMap.n_keys_for_partition)
    def n_keys_for_partition(self, partition):
        if partition not in self._n_keys_map:
            raise PacmanNotExistException(
                self.NOT_EXIST_ERROR_MESSAGE.format(partition))
        return self._n_keys_map[partition]

    @overrides(AbstractMachinePartitionNKeysMap.__iter__)
    def __iter__(self):
        return iter(self._n_keys_map)
