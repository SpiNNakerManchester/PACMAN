# Copyright (c) 2020-2023 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from spinn_utilities.abstract_base import abstractmethod, AbstractBase


class AbstractSDRAMPartition(object, metaclass=AbstractBase):
    """ An edge partition that contains SDRAM edges.
    """

    @abstractmethod
    def total_sdram_requirements(self):
        """ Get the total SDRAM required by this outgoing partition.

        :return: int
        """

    @abstractmethod
    def get_sdram_base_address_for(self, vertex):
        """ Get the SDRAM base address for a edge given which side \
            the vertex is on.

        :param vertex: the vertex to find SDRAM base address of
        :return: the SDRAM address for this vertex
        """

    @abstractmethod
    def get_sdram_size_of_region_for(self, vertex):
        """ Get the size of the region for a vertex given a edge.

        :param vertex: the vertex to find SDRAM size of
        :return: the SDRAM size for this vertex
        """
