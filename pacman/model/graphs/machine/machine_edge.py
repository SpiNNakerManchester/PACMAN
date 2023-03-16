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


class MachineEdge(AbstractEdge):
    """
    A simple implementation of a machine edge.
    """

    __slots__ = [
        # The vertex at the start of the edge
        "_pre_vertex",

        # The vertex at the end of the edge
        "_post_vertex",

        # The label of the edge
        "_label"
    ]

    def __init__(self, pre_vertex, post_vertex, label=None):
        """
        :param MachineVertex pre_vertex: The vertex at the start of the edge.
        :param MachineVertex post_vertex: The vertex at the end of the edge.
        :param label: The name of the edge.
        :type label: str or None
        """
        self._label = label
        self._pre_vertex = pre_vertex
        self._post_vertex = post_vertex

    @property
    @overrides(AbstractEdge.label)
    def label(self):
        return self._label

    @property
    @overrides(AbstractEdge.pre_vertex, extend_doc=False)
    def pre_vertex(self):
        """
        The vertex at the start of the edge.

        :rtype: ~pacman.model.graphs.machine.MachineVertex
        """
        return self._pre_vertex

    @property
    @overrides(AbstractEdge.post_vertex, extend_doc=False)
    def post_vertex(self):
        """
        The vertex at the end of the edge.

        :rtype: ~pacman.model.graphs.machine.MachineVertex
        """
        return self._post_vertex

    def __repr__(self):
        return (
            "MachineEdge(pre_vertex={}, post_vertex={}, label={})".format(
                self._pre_vertex, self._post_vertex, self.label))
