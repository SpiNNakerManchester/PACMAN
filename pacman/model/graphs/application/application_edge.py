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

from spinn_utilities.overrides import overrides
from pacman.model.graphs import AbstractEdge


class ApplicationEdge(AbstractEdge):
    """
    A simple implementation of an application edge.
    """

    __slots__ = [
        # The edge at the start of the vertex
        "_pre_vertex",

        # The edge at the end of the vertex
        "_post_vertex",

        # The label
        "_label"
    ]

    def __init__(self, pre_vertex, post_vertex, label=None):
        """
        :param ApplicationVertex pre_vertex:
            The application vertex at the start of the edge.
        :param ApplicationVertex post_vertex:
            The application vertex at the end of the edge.
        :param label: The name of the edge.
        :type label: str or None
        :param machine_edge_type:
            The type of machine edges made from this app edge. If ``None``,
            standard machine edges will be made.
        :type machine_edge_type: type(MachineEdge)
        """
        self._label = label
        self._pre_vertex = pre_vertex
        self._post_vertex = post_vertex

    @property
    @overrides(AbstractEdge.label)
    def label(self):
        return self._label

    @property
    @overrides(AbstractEdge.pre_vertex)
    def pre_vertex(self):
        return self._pre_vertex

    @property
    @overrides(AbstractEdge.post_vertex)
    def post_vertex(self):
        return self._post_vertex
