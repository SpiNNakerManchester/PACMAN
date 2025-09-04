# Copyright (c) 2019 The University of Manchester
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
from __future__ import annotations
from typing import Optional, FrozenSet, TYPE_CHECKING
from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from pacman.model.resources import AbstractSDRAM
from pacman.model.graphs.common import Slice
if TYPE_CHECKING:
    from pacman.model.graphs.machine import MachineVertex


# Can't use this decorator: circular import problem
# @require_subclass(ApplicationVertex)
class LegacyPartitionerAPI(object, metaclass=AbstractBase):
    """
    API used by the vertices which don't have their own splitters but use
    what master did before the self partitioning stuff came to be.

    .. warning::
        Subclasses of this class must also be subclasses of
        :py:class:`ApplicationVertex`. This is not enforced because of issues
        with import order, but is required; PACMAN assumes it to be true.
    """
    __slots__ = ()

    @abstractmethod
    def get_sdram_used_by_atoms(self, vertex_slice: Slice) -> AbstractSDRAM:
        """
        :param vertex_slice:
            the low value of atoms to calculate resources from
        :returns: The separate SDRAM requirements for a range of atoms.
        """
        raise NotImplementedError

    @abstractmethod
    def create_machine_vertex(
            self, vertex_slice: Slice, sdram: AbstractSDRAM,
            label: Optional[str] = None) -> MachineVertex:
        """
        Create a machine vertex from this application vertex.

        :param vertex_slice:
            The slice of atoms that the machine vertex will cover.
        :param sdram:
            The SDRAM used by the machine vertex.
        :param label: human readable label for the machine vertex
        :return: The created machine vertex
        """
        raise NotImplementedError

    @staticmethod
    def abstract_methods() -> FrozenSet[str]:
        """
        :returns: The abstract methods and properties defined in this class.
        """
        return LegacyPartitionerAPI.\
            __abstractmethods__  # type: ignore[attr-defined]
