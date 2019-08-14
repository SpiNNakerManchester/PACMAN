# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from pacman.exceptions import PacmanConfigurationException
from pacman.model.graphs.common import ConstrainedObject


class AbstractVertex(ConstrainedObject):
    """ A vertex in a graph.
    """

    # Because of diamond inheritance slots must be empty
    __slots__ = [
        # Indicates if the Vertex has been added to a graph
        "_added_to_graph",
        # Label for the vertex. Changable until added to graph
        "_label"]

    def __init__(self, label=None, constraints=None):
        """
        :param label: The optional name of the vertex
        :type label: str
        :param constraints: The optional initial constraints of the vertex
        :type constraints: \
            iterable(:py:class:`pacman.model.constraints.AbstractConstraint`)
        :raise pacman.exceptions.PacmanInvalidParameterException:\
            * If one of the constraints is not valid
        """

        super(AbstractVertex, self).__init__(constraints)
        self._label = label
        self._added_to_graph = False

    @property
    def label(self):
        """
        Returns the current label to the vertex.

        This label could change when the vertex is added to the graph.
        :return: The label
        :rtype: str
        """
        return self._label

    def set_label(self, label):
        """
        Changes the label for a vertex NOT yet ADDED to a graph

        :param label: new value for the label
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
        Records that the vertex has been added to a graph
        :raises PacmanConfigurationException:
            If there is an attempt to add the same vertex more than once
        """
        if self._added_to_graph:
            raise PacmanConfigurationException("Already added to a graph")
        self._added_to_graph = True
