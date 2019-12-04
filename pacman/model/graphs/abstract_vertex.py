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
from spinn_utilities.abstract_base import (
    abstractproperty, AbstractBase)
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
        :raises PacmanConfigurationException: \
            If there is an attempt to change the label once the vertex has \
            been added to a graph
        """
        if self._added_to_graph:
            raise PacmanConfigurationException(
                "As Labels are also IDs they can not be changed.")
        self._label = label

    def addedToGraph(self):
        """
        Records that the vertex has been added to a graph

        :raises PacmanConfigurationException: \
            If there is an attempt to add the same vertex more than once
        """
        self._added_to_graph = True

    @abstractproperty
    def timestep_in_us(self):
        """ The timestep of this vertex in us

        Typically will default to the machine timestep

        If the machine vertexes have different timestemps this method will\
        return the lowest common multiple of these

        :rtype: int
        """

    def simtime_in_us_to_timesteps(self, simtime_in_us):
        """
        Helper function to convert simtime in us to whole timestep

        This function verfies that the simtime is a multile of the timestep.

        :param simtime_in_us: a simulation time in us
        :type simtime_in_us: int
        :return: the exact number of timeteps covered by this simtime
        :rtype: int
        :raises ValueError: If the simtime is not a mutlple of the timestep
        """
        n_timesteps = simtime_in_us // self.timestep_in_us
        check = n_timesteps * self.timestep_in_us
        if check != simtime_in_us:
            raise ValueError(
                "The requested time {} is not a multiple of the timestep {}"
                "".format(simtime_in_us, self.timestep_in_us))
        return n_timesteps
