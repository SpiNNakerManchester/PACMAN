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
from typing import Generic, Optional, TypeVar
from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from .abstract_vertex import AbstractVertex

#: :meta private:
V = TypeVar("V", bound=AbstractVertex)


class AbstractEdge(Generic[V], metaclass=AbstractBase):
    """
    A directed edge in a graph between two vertices.
    """

    __slots__ = ()

    @property
    @abstractmethod
    def label(self) -> Optional[str]:
        """
        The label of the edge.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def pre_vertex(self) -> V:
        """
        The vertex at the start of the edge.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def post_vertex(self) -> V:
        """
        The vertex at the end of the edge.
        """
        raise NotImplementedError
