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

from pacman.exceptions import PacmanConfigurationException
from pacman.model.graphs.common import ChipAndCore


class AbstractVertex(object):
    """
    A vertex in a graph.
    """

    __slots__ = [
        # Indicates if the Vertex has been added to a graph
        "_added_to_graph",
        # Label for the vertex. Changable until added to graph
        "_label",
        # the x, y (and p) this vertex MUST be placed on
        "_fixed_location"
    ]

    def __init__(self, label=None):
        """
        :param str label: The optional name of the vertex
        """
        self._label = label
        self._added_to_graph = False
        self._fixed_location = None

    @property
    def label(self):
        """
        The current label to the vertex.

        This label could change when the vertex is added to the graph.

        :rtype: str
        """
        return self._label

    def set_label(self, label):
        """
        Changes the label for a vertex *not yet added* to a graph.

        :param str label: new value for the label
        :raises PacmanConfigurationException:
            If there is an attempt to change the label once the vertex has
            been added to a graph
        """
        if self._added_to_graph:
            raise PacmanConfigurationException(
                "As Labels are also IDs they can not be changed.")
        self._label = label

    def addedToGraph(self):
        """
        Records that the vertex has been added to a graph.

        :raises PacmanConfigurationException:
            If there is an attempt to add the same vertex more than once
        """
        self._added_to_graph = True

    def get_fixed_location(self):
        """
        The x, y and possibly p the vertex *must* be placed on.

        Typically `None`! Does not have the value of a normal placements.

        Used instead of `ChipAndCoreConstraint`.

        :rtype: None or ~pacman.model.graphs.common.ChipAndCore
        """
        return self._fixed_location

    def set_fixed_location(self, x, y, p=None):
        """
        Set the location where the vertex must be placed.

        .. note::
            If called, must be called prior to the placement algorithms.

        :param int x: X coordinate of fixed location
        :param int y: Y coordinate of fixed location
        :param int p: Processor ID of fixed location
        :raises PacmanConfigurationException:
            If a fixed location has already been set to a different location.
        """
        fixed_location = ChipAndCore(x, y, p)
        if self._fixed_location is not None:
            if fixed_location == self._fixed_location:
                return
            raise PacmanConfigurationException(
                "Once set to a value fixed_location can not be changed")
        self._fixed_location = fixed_location
