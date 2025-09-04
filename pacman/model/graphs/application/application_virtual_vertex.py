# Copyright (c) 2022 The University of Manchester
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
from spinn_utilities.abstract_base import abstractmethod
from spinn_machine import Machine
from spinn_machine.link_data_objects import AbstractLinkData
from .application_vertex import ApplicationVertex


class ApplicationVirtualVertex(ApplicationVertex):
    """
    An application vertex which is virtual.
    """

    __slots__ = ()

    @abstractmethod
    def get_outgoing_link_data(self, machine: Machine) -> AbstractLinkData:
        """
        Get the link data for outgoing connections from the machine.

        :param machine: The machine to get the link data from
        :returns: the outgoing link data of the vertex's type
        """
        raise NotImplementedError
