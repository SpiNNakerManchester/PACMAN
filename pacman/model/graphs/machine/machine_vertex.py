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
from pacman.model.graphs import AbstractVertex
from pacman.model.graphs.common import Slice
from pacman.model.graphs.application import ApplicationVertex


@add_metaclass(AbstractBase)
class MachineVertex(AbstractVertex):
    """ A machine graph vertex.
    """

    __slots__ = ["_app_vertex", "_index", "_vertex_slice"]
    _DEFAULT_SLICE = Slice(0, 0)

    def __init__(self, label=None, constraints=None, app_vertex=None,
                 vertex_slice=None):
        """
        :param label: The optional name of the vertex
        :type label: str or None
        :param iterable(AbstractConstraint) constraints:
            The optional initial constraints of the vertex
        :param app_vertex:
            The application vertex that caused this machine vertex to be
            created. If None, there is no such application vertex.
        :type app_vertex: ApplicationVertex or None
        :param vertex_slice:
            The slice of the application vertex that this machine vertex
            implements.
        :type vertex_slice: Slice or None
        :raise PacmanInvalidParameterException:
            If one of the constraints is not valid
        :raises PacmanValueError: If the slice of the machine_vertex is too big
        :raise AttributeError:
            If a not None app_vertex is not an ApplicationVertex
        """
        if label is None:
            label = str(type(self))
        super(MachineVertex, self).__init__(label, constraints)
        self._added_to_graph = False
        self._app_vertex = app_vertex
        self._index = None
        if vertex_slice is not None:
            self._vertex_slice = vertex_slice
        else:
            self._vertex_slice = self._DEFAULT_SLICE
        # associate depends on self._vertex_slice and self._app_vertex
        self.associate_application_vertex()

    def associate_application_vertex(self):
        """
        Asks the application vertex (if any) to remember this machine vertex.
        :raises PacmanValueError: If the slice of the machine_vertex is too big
        """
        # remember depends on slice already being set
        if self._app_vertex:
            self._app_vertex.remember_associated_machine_vertex(self)

    @property
    def app_vertex(self):
        """ The application vertex that caused this machine vertex to be
            created. If None, there is no such application vertex.

        :rtype: ApplicationVertex or None
        """
        return self._app_vertex

    @property
    def vertex_slice(self):
        """ The slice of the application vertex that this machine vertex
            implements.

        :rtype: Slice
        """
        return self._vertex_slice

    @property
    def index(self):
        """ The index into the collection of machine vertices for an
            application vertex.

        :rtype: int
        """
        return self._index if self._index is not None else 0

    @index.setter
    def index(self, value):
        """ The index into the collection of machine vertices for an
            application vertex.
        """
        self._index = value

    def __str__(self):
        _l = self.label
        return self.__repr__() if _l is None else _l

    def __repr__(self):
        if self.constraints:
            return "MachineVertex(label={}, constraints={})".format(
                self.label, self.constraints)
        return "MachineVertex(label={})".format(self.label)

    @abstractproperty
    def resources_required(self):
        """ The resources required by the vertex

        :rtype: ~pacman.model.resources.ResourceContainer
        """
