# Copyright (c) 2020 The University of Manchester
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
from spinn_utilities.abstract_base import abstractmethod, AbstractBase
from .machine_vertex import MachineVertex


class AbstractSysRAMPartition(object, metaclass=AbstractBase):
    """
    An edge partition that contains SysRAM edges.
    """
    __slots__ = ()

    @abstractmethod
    def total_sysram_requirements(self) -> int:
        """
        Get the total SysRAM required by this outgoing partition.

        :return: int
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def sysram_base_address(self) -> int:
        """
        The base address of the SysRAM piece used for communication.
        """
        raise NotImplementedError

    @sysram_base_address.setter
    def sysram_base_address(self, new_value: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_sysram_base_address_for(self, vertex: MachineVertex) -> int:
        """
        Get the SysRAM base address for a edge given which side
        the vertex is on.

        :param vertex: the vertex to find SysRAM base address of
        :return: the SysRAM address for this vertex
        """
        raise NotImplementedError

    @abstractmethod
    def get_sysram_size_of_region_for(self, vertex: MachineVertex) -> int:
        """
        Get the size of the region for a vertex given a edge.

        :param vertex: the vertex to find SysRAM size of
        :return: the SysRAM size for this vertex
        """
        raise NotImplementedError
