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

from six import add_metaclass
from spinn_utilities.abstract_base import (AbstractBase)
from pacman.exceptions import PacmanConfigurationException
from pacman.model.graphs.common import ConstrainedObject


@add_metaclass(AbstractBase)
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
        :param str label: The optional name of the vertex
        :param iterable(AbstractConstraint) constraints:
            The optional initial constraints of the vertex
        :raise PacmanInvalidParameterException:
            If one of the constraints is not valid
        """

        super(AbstractVertex, self).__init__(constraints)
        self._label = label
        self._added_to_graph = False

    @property
    def label(self):
        """ The current label to the vertex.

        This label could change when the vertex is added to the graph.

        :rtype: str
        """
        return self._label

    def set_label(self, label):
        """ Changes the label for a vertex *not yet added* to a graph.

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
        """ Records that the vertex has been added to a graph

        :raises PacmanConfigurationException:
            If there is an attempt to add the same vertex more than once
        """
        self._added_to_graph = True
