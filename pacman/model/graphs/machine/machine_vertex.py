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

from spinn_utilities.abstract_base import AbstractBase, abstractproperty
from spinn_utilities.overrides import overrides
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
        """
        The application vertex that caused this machine vertex to be
        created. If `None`, there is no such application vertex.

        :rtype: ApplicationVertex or None
        """
        return self._app_vertex

    @property
    def vertex_slice(self):
        """
        The slice of the application vertex that this machine vertex
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
        # pylint: disable=unused-argument
        return 1 << get_n_bits_for_fields(self._vertex_slice.shape)

    @property
    def index(self):
        """
        The index into the collection of machine vertices for an
        application vertex.

        :rtype: int
        """
        return self._index if self._index is not None else 0

    @index.setter
    def index(self, value):
        """
        The index into the collection of machine vertices for an
        application vertex.
        """
        self._index = value

    def __str__(self):
        _l = self.label
        return self.__repr__() if _l is None else _l

    def __repr__(self):
        if self.get_fixed_location():
            return f"MachineVertex({self.label}, " \
                   f"at{self.get_fixed_location()})"
        else:
            return f"MachineVertex({self.label})"

    @abstractproperty
    def sdram_required(self):
        """ The SDRAM space required by the vertex.

        :rtype: ~pacman.model.resources.AbstractSDRAM
        """

    @property
    def iptags(self):
        """
        The IPtags used by this vertex if any.

        :rtype: iterable(IPtagResource)
        """
        return []

    @property
    def reverse_iptags(self):
        """
        The reverse IPtags used by this vertex if any.

        :rtype: iterable(ReverseIPtagResource)
        """
        return []

    @overrides(AbstractVertex.get_fixed_location)
    def get_fixed_location(self):
        """
        The x, y and possibly p the vertex *must* be placed on.

        Typically `None`! Does not have the value of a normal placememts.

        If the Machine vertex has no fixed_location
        but does have an app_vertex, app_vertex.fixed_location is used.
        If both have a fixed_location the app level is ignored!

        Used instead of ChipAndCoreConstraint

        :rtype: None or ChipAndCore
        """
        if self._fixed_location:
            return self._fixed_location
        if self._app_vertex:
            return self._app_vertex.get_fixed_location()
        return None
