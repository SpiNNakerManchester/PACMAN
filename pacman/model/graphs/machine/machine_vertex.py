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
from pacman.model.graphs import AbstractVertex
from pacman.model.graphs.common import ConstrainedObject
from pacman.model.graphs.application import ApplicationVertex
from pacman.exceptions import PacmanInvalidParameterException


@add_metaclass(AbstractBase)
class MachineVertex(ConstrainedObject, AbstractVertex):
    """ A machine graph vertex.
    """

    __slots__ = ["_app_vertex", "_label"]

    def __init__(self, label=None, constraints=None, app_vertex=None):
        """
        :param label: The optional name of the vertex
        :type label: str
        :param constraints: The optional initial constraints of the vertex
        :type constraints: \
            iterable(:py:class:`pacman.model.constraints.AbstractConstraint`)
        :param app_vertex: The application vertex that caused this machine\
            vertex to be created. If None, there is no such application vertex.
        :raise pacman.exceptions.PacmanInvalidParameterException:
            * If one of the constraints is not valid
        """
        super(MachineVertex, self).__init__(constraints)
        if label:
            self._label = label
        else:
            self._label = str(type(self))
        self._app_vertex = app_vertex
        if app_vertex is not None and not isinstance(
                app_vertex, ApplicationVertex):
            raise PacmanInvalidParameterException(
                "app_vertex", app_vertex,
                "must be an application vertex")

    @property
    @overrides(AbstractVertex.label)
    def label(self):
        return self._label

    @property
    def app_vertex(self):
        return self._app_vertex

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
