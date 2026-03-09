# Copyright (c) 2021 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from typing import Optional
import numpy

from spinn_utilities.abstract_base import abstractmethod

from pacman.exceptions import PacmanConfigurationException, PacmanValueError
from pacman.model.graphs import AbstractVertex
from pacman.utilities.constants import BITS_IN_KEY, FULL_MASK
from pacman.utilities.utility_calls import calc_shift

from .base_key_and_mask import BaseKeyAndMask

NOT_SET = -1000


class VertexRoutingInfo(object):
    """
    Associates a partition identifier to its routing information
    (keys and masks).
    """

    __global_application_mask = NOT_SET  # temp value until set
    __global_machine_mask = NOT_SET  # temp value until set

    __slots__ = (
        # The partition identifier of the allocation
        "__partition_id")

    def __init__(self, partition_id: str):
        """
        :param partition_id: The partition to set the keys for
        """
        self.__partition_id = partition_id

    def get_keys(self, n_keys: Optional[int] = None) -> numpy.ndarray:
        """
        Get the ordered list of individual keys allocated to the edge.

        :param n_keys: Optional limit on the number of keys to return
        :return: An array of keys
        """
        max_n_keys = self.key_and_mask.n_keys

        if n_keys is None:
            n_keys = max_n_keys
        elif max_n_keys < n_keys:
            raise PacmanConfigurationException(
                f"You asked for {n_keys} keys, but the routing info can only "
                f"provide {max_n_keys} keys.")

        key_array = numpy.zeros(n_keys, dtype=">u4")
        offset = 0
        _, offset = self.key_and_mask.get_keys(
            key_array=key_array, offset=offset, n_keys=(n_keys - offset))
        return key_array

    @property
    @abstractmethod
    def key_and_mask(self) -> BaseKeyAndMask:
        """
        The only key and mask.
        """

    @property
    def key(self) -> int:
        """
        The first key (or only one if there is only one).
        """
        return self.key_and_mask.key

    @property
    def mask(self) -> int:
        """
        The first mask (or only one if there is only one).
        """
        return self.key_and_mask.mask

    @property
    def partition_id(self) -> str:
        """
        The identifier of the partition.
        """
        return self.__partition_id

    @property
    @abstractmethod
    def vertex(self) -> AbstractVertex:
        """
        The vertex of the information.
        """
        raise NotImplementedError

    @property
    def atom_mask(self) -> int:
        """
        The mask for the atom zone

        This is the inverse of the Machine mask
        """
        return self.machine_mask ^ FULL_MASK

    @property
    @abstractmethod
    def atom_shift(self) -> int:
        """
        The shitf for the atom zone.

        Likely zero or None

        :raises PacmanValueError: If the mask is not shiftable
        """

    @property
    @abstractmethod
    def machine_mask(self) -> int:
        """
        The machine mask as reported by the vertex

        This includes both the Application index and the machine index
        """

    @property
    @abstractmethod
    def machine_shift(self) -> int:
        """
        The shift for the machine zone.

        :raises PacmanValueError: If the mask is not shiftable
        """
        return calc_shift(self.machine_mask)

    @property
    @abstractmethod
    def app_mask(self) -> int:
        """
        The application mask as reported by the vertex
        """

    @property
    @abstractmethod
    def app_shift(self) -> int:
        """
        The shift for the application zone.

        :raises PacmanValueError: If the mask is not shiftable
        """
        return calc_shift(self.app_mask)

    @property
    def machine_index_mask(self) -> int:
        """
        The mask for the zone with the machine index.

        Semantic sugar for app mask minus the machine mask.

        This includes ONLY the machine index and not the Application index.

        May be an empty mask for fixed vertices with one app one Machine
        """
        return self.app_mask ^ self.machine_mask

    @property
    @abstractmethod
    def has_fixed_keys(self) -> bool:
        """
        True if the vertex requires fixed

        Fixed keys may be shiftable and even global
        """

    @property
    @abstractmethod
    def has_shiftable_masks(self):
        """
        True if all masks are shiftable.

        Only fixed key vertices should have none shiftable masks
        """

    @property
    @abstractmethod
    def has_global_masks(self):
        """
        True if all masks are the global ones defined by the zones

        Global masks are always shiftable.
        """

    @classmethod
    def set_global_mask(cls, app_mask: int, machine_mask) -> None:
        """
        Sets the global masks once the allocator has picked them
        """
        cls.__global_application_mask = app_mask
        cls.__global_machine_mask = machine_mask

    @classmethod
    def get_global_application_mask(cls) -> int:
        """
        The global application mask use by the allocator.

        As this is a class method this is reproted by ll infos even
        ones that do not respect it.

        :returns: The global masked
        """
        return cls.__global_application_mask

    @classmethod
    def get_global_machine_mask(cls) -> int:
        """
        The global machine mask used by the allocator

        As this is a class method this is reproted by ll infos even
        ones that do not respect it.

        :returns: The global masked
        """
        return cls.__global_machine_mask
