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

from spinn_utilities.abstract_base import abstractmethod, AbstractBase

from pacman.exceptions import PacmanConfigurationException
from pacman.model.graphs import AbstractVertex
from pacman.utilities.constants import FULL_MASK
from pacman.utilities.utility_calls import calc_shift

from .base_key_and_mask import BaseKeyAndMask
from ..graphs.application import ApplicationVertex

NOT_SET = -1000


class VertexRoutingInfo(object, metaclass=AbstractBase):
    """
    Associates a partition identifier to its routing information
    (keys and masks).
    """

    _global_application_mask = NOT_SET  # temp value until set
    _global_machine_mask = NOT_SET  # temp value until set

    __slots__ = (
        # The key of this routing info
        "_key",
        # Mask may be global or specific so not included here
        # The partition identifier of the allocation
        "__partition_id",)

    def __init__(self, key: int, partition_id: str):
        """
        :param partition_id: The partition to set the keys for
        """
        self._key = key
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
    def key_and_mask(self) -> BaseKeyAndMask:
        """
        The only key and mask.
        """
        return BaseKeyAndMask(self.key, self.mask)

    @property
    def key(self) -> int:
        """
        The key for this info
        """
        return self._key

    @property
    @abstractmethod
    def mask(self) -> int:
        """
        The mask for this info
        """
        raise NotImplementedError

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
    @abstractmethod
    def app_vertex(self) -> ApplicationVertex:
        """
        The Application vertex of the information.

        If the vertex is a Machine Vertex returns its application vertex
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
    def n_bits_atoms(self) -> int:
        """
        The number of bits for the atoms.

        Semantic sugar for machine_shift

        :raises PacmanValueError: If the masks are not shiftable
        """
        return self.machine_shift

    @property
    def app_mask(self) -> int:
        """
        The application mask for the vertices

        This includes both the Application index and the machine index
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def machine_mask(self) -> int:
        """
        The machine mask as reported by the vertex

        This includes both the Application index and the machine index
        """
        raise NotImplementedError()

    @property
    def machine_shift(self) -> int:
        """
        The shift for the machine zone.

        :raises PacmanValueError: If the mask is not shiftable
        """
        return calc_shift(self.machine_mask)

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
        raise NotImplementedError()

    @property
    def has_global_masks(self) -> bool:
        """
        True if all masks are the global ones defined by the zones

        Application Masks always are so this is about Machine Masks
        """
        return self.has_global_app_masks and self.has_global_machine_masks

    @property
    @abstractmethod
    def has_global_app_masks(self) -> bool:
        """
        True if all masks are the global ones defined by the zones

        Application Masks always are so this is about Machine Masks
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def has_global_machine_masks(self) -> bool:
        """
        True if all masks are the global ones defined by the zones

        Application Masks always are so this is about Machine Masks
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def has_app_keys_overlap(self) -> bool:
        """
        True unless the allocator has marked this info as having an overlap
        """
        raise NotImplementedError()

    @abstractmethod
    def set_app_keys_overlap(self) -> None:
        """
        Flags the info as sharing an app key with another info

        That is the key here shifted by the global app shit will result in the
        same value as another info with a different app_vertex or partition ID
        """
        raise NotImplementedError()

    @classmethod
    def set_global_mask(cls, app_mask: int, machine_mask: int) -> None:
        """
        Sets the global masks once the allocator has picked them
        """
        cls._global_application_mask = app_mask
        cls._global_machine_mask = machine_mask

    @classmethod
    def get_global_app_shift(cls) -> int:
        """
        The shift global for the application zone.

        This is a class method so will be the same value for all Vertices.

        For Fixed Masks this may not be the shift of the actual Application
        mask but is a value that will work.

        :returns: The global shift for the application zone.
        """
        return calc_shift(cls._global_application_mask)

    @classmethod
    def get_global_app_mask(cls) -> int:
        """
        The global application mask used by the allocator

        As this is a class method this is reported by all infos even
        ones that do not respect it.

        :returns: The global masked
        """
        return cls._global_application_mask

    @classmethod
    def get_global_machine_mask(cls) -> int:
        """
        The global machine mask used by the allocator

        As this is a class method this is reported by all infos even
        ones that do not respect it.

        :returns: The global masked
        """
        return cls._global_machine_mask
