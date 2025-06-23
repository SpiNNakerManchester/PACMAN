# Copyright (c) 2016 The University of Manchester
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
from typing import Iterable, Optional, final, TYPE_CHECKING
from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from spinn_utilities.overrides import overrides
from pacman.model.graphs import AbstractVertex
from pacman.model.graphs.common import Slice
from pacman.utilities.utility_calls import get_n_bits
if TYPE_CHECKING:
    from pacman.model.graphs.application import ApplicationVertex
    from pacman.model.resources import AbstractSDRAM
    from pacman.model.resources import IPtagResource
    from pacman.model.resources import ReverseIPtagResource
    from pacman.model.graphs.common import ChipAndCore


class MachineVertex(AbstractVertex, metaclass=AbstractBase):
    """
    A machine graph vertex.
    """

    __slots__ = (
        "_app_vertex", "_index", "__vertex_slice")
    _DEFAULT_SLICE = Slice(0, 0)

    def __init__(self, label: Optional[str] = None,
                 app_vertex: Optional[ApplicationVertex] = None,
                 vertex_slice: Optional[Slice] = None):
        """
        :param label: The optional name of the vertex
        :param app_vertex:
            The application vertex that caused this machine vertex to be
            created. If `None`, there is no such application vertex.
        :param vertex_slice:
            The slice of the application vertex that this machine vertex
            implements.
        :raises PacmanValueError: If the slice of the machine_vertex is too big
        :raise AttributeError:
            If a not-`None` app_vertex is not an ApplicationVertex
        """
        if label is None:
            label = str(type(self))
        super().__init__(label)
        self._added_to_graph = False
        self._app_vertex = app_vertex
        self._index: Optional[int] = None
        if vertex_slice is not None:
            self.__vertex_slice = vertex_slice
        else:
            self.__vertex_slice = self._DEFAULT_SLICE

    @property
    def app_vertex(self) -> Optional[ApplicationVertex]:
        """
        The application vertex that caused this machine vertex to be
        created. If `None`, there is no such application vertex.
        """
        return self._app_vertex

    @property
    @final
    def vertex_slice(self) -> Slice:
        """
        The slice of the application vertex that this machine vertex
        implements.
        """
        return self.__vertex_slice

    def get_n_keys_for_partition(self, partition_id: str) -> int:
        """
        Get the number of keys required by the given partition of edges.

        :param partition_id: The identifier of the partition; the
            partition_id param is only used by some MachineVertex subclasses
        :return: The number of keys required
        """
        _ = partition_id
        return 1 << get_n_bits(self.__vertex_slice.n_atoms)

    @property
    def index(self) -> int:
        """
        The index into the collection of machine vertices for an
        application vertex.
        """
        return self._index if self._index is not None else 0

    @index.setter
    def index(self, value: int) -> None:
        """
        The index into the collection of machine vertices for an
        application vertex.
        """
        self._index = value

    def __str__(self) -> str:
        _l = self.label
        return self.__repr__() if _l is None else _l

    def __repr__(self) -> str:
        if self.get_fixed_location():
            return (f"MachineVertex({self.label}, "
                    f"at{self.get_fixed_location()})")
        else:
            return f"MachineVertex({self.label})"

    @property
    @abstractmethod
    def sdram_required(self) -> AbstractSDRAM:
        """
        The SDRAM space required by the vertex.
        """
        raise NotImplementedError

    @property
    def iptags(self) -> Iterable[IPtagResource]:
        """
        The :py:class:`~spinn_machine.tags.IPTag`\\s used by this vertex,
        if any.
        """
        return []

    @property
    def reverse_iptags(self) -> Iterable[ReverseIPtagResource]:
        """
        The :py:class:`~spinn_machine.tags.ReverseIPTag`\\s used by this
        vertex, if any.
        """
        return []

    @overrides(AbstractVertex.get_fixed_location)
    def get_fixed_location(self) -> Optional[ChipAndCore]:
        """
        .. note::
            If the Machine vertex has no `fixed_location`
            but does have an `app_vertex`, `app_vertex.fixed_location` is used.
            If both have a `fixed_location` the app level is ignored!
        """
        if self._fixed_location:
            return self._fixed_location
        if self._app_vertex:
            return self._app_vertex.get_fixed_location()
        return None
