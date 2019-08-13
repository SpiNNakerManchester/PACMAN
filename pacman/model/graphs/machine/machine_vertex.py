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
from spinn_utilities.abstract_base import AbstractBase, abstractproperty
from spinn_utilities.overrides import overrides
from pacman.exceptions import PacmanConfigurationException
from pacman.model.graphs import AbstractVertex
from pacman.model.graphs.common import ConstrainedObject


@add_metaclass(AbstractBase)
class MachineVertex(ConstrainedObject, AbstractVertex):
    """ A machine graph vertex.
    """

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
        :raise pacman.exceptions.PacmanInvalidParameterException:
            * If one of the constraints is not valid
        """
        ConstrainedObject.__init__(self, constraints)
        if label:
            self._label = label
        else:
            self._label = str(type(self))
        self._added_to_graph = False

    @property
    @overrides(AbstractVertex.label)
    def label(self):
        return self._label

    @property
    @overrides(AbstractVertex.label)
    def label(self):
        """
        Returns the current label to the vertex.

        This label could change when the vertex is added to the graph.
        :return: The label
        """
        return self._label

    @overrides(AbstractVertex.set_label)
    def set_label(self, label):
        if self._added_to_graph:
            raise PacmanConfigurationException(
                "As Labels are also IDs they can not be changed.")

    @overrides(AbstractVertex.addedToGraph)
    def addedToGraph(self):
        if self._added_to_graph:
            raise PacmanConfigurationException("Already added to a graph")

    def __str__(self):
        _l = self.label
        return self.__repr__() if _l is None else _l

    def __repr__(self):
        return "MachineVertex(label={}, constraints={}".format(
            self.label, self.constraints)

    @abstractproperty
    def resources_required(self):
        """ The resources required by the vertex

        :rtype: :py:class:`pacman.model.resources.ResourceContainer`
        """
