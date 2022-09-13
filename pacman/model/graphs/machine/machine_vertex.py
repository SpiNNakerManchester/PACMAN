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

from spinn_utilities.abstract_base import AbstractBase, abstractproperty
from pacman.model.graphs import AbstractVertex
from pacman.model.graphs.common import Slice
from pacman.utilities.utility_calls import get_n_bits_for_fields


class MachineVertex(AbstractVertex, metaclass=AbstractBase):
    """ A machine graph vertex.
    """

    __slots__ = ["_app_vertex", "_index", "_vertex_slice"]
    _DEFAULT_SLICE = Slice(0, 0)

    def __init__(self, label=None, app_vertex=None, vertex_slice=None):
        """
        :param label: The optional name of the vertex
        :type label: str or None
        :param app_vertex:
            The application vertex that caused this machine vertex to be
            created. If None, there is no such application vertex.
        :type app_vertex: ApplicationVertex or None
        :param vertex_slice:
            The slice of the application vertex that this machine vertex
            implements.
        :type vertex_slice: Slice or None
        :raises PacmanValueError: If the slice of the machine_vertex is too big
        :raise AttributeError:
            If a not None app_vertex is not an ApplicationVertex
        """
        if label is None:
            label = str(type(self))
        super().__init__(label)
        self._added_to_graph = False
        self._app_vertex = app_vertex
        self._index = None
        if vertex_slice is not None:
            self._vertex_slice = vertex_slice
        else:
            self._vertex_slice = self._DEFAULT_SLICE

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

    def get_n_keys_for_partition(self, partition_id):
        """ Get the number of keys required by the given partition of edges.

        :param str partition_id: The identifier of the partition
            partition_id param is only used by some MachineVertex clases
        :return: The number of keys required
        :rtype: int
        """
        return 1 << get_n_bits_for_fields(self._vertex_slice.shape)

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
        if self.fixed_location:
            return f"MachineVertex({self.label}, at{self.fixed_location})"
        else:
            return f"MachineVertex({self.label})"

    @abstractproperty
    def sdram_required(self):
        """ The sdram required by the vertex

        :rtype: ~pacman.model.resources.AbstractSDRAM
        """

    @property
    def iptags(self):
        """
        The iptags used by this vertex if any.

        :rtype: iterable(IPtagResource)
        """
        return []

    @property
    def reverse_iptags(self):
        """
        The reverse iptags used by this vertex if any.

        :rtype: iterable(ReverseIPtagResource)
        """
        return []

    @property
    def fixed_location(self):
        """
        The x, y and possibly p the vertex MUST be placed on.

        Typically NONE! Does not have the value of a normal placememts.

        If the Machine vertex has no fixed_location
        but does have an app_vertex, app_vertex.fixed_location is used.
        If both have a fixed_location the app level is ignored!

        Used instead of ChipAndCoreConstraint

        :rtype: None or ChipAndCore
        """
        if self._fixed_location:
            return self._fixed_location
        if self._app_vertex:
            return self._app_vertex._fixed_location
        return None
