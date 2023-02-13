# Copyright (c) 2016-2023 The University of Manchester
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
from spinn_utilities.abstract_base import AbstractBase, abstractproperty


class AbstractEdge(object, metaclass=AbstractBase):
    """ A directed edge in a graph between two vertices.
    """

    __slots__ = ()

    @abstractproperty
    def label(self):
        """ The label of the edge

        :rtype: str
        """

    @abstractproperty
    def pre_vertex(self):
        """ The vertex at the start of the edge

        :rtype: AbstractVertex
        """

    @abstractproperty
    def post_vertex(self):
        """ The vertex at the end of the edge

        :rtype: AbstractVertex
        """
