# Copyright (c) 2019-2020 The University of Manchester
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
from spinn_utilities.abstract_base import AbstractBase, abstractmethod


@add_metaclass(AbstractBase)
class AbstractControlsSourceOfEdges(object):

    def __init__(self):
        pass

    @abstractmethod
    def get_sources_for_edge_from(
            self, app_edge, partition_id, graph_mapper,
            original_source_machine_vertex):
        """ allows a vertex to decide which of its internal machine vertices \
        sends a given machine edge

        :param app_edge: the application edge
        :param partition_id: the outgoing partition id
        :param graph_mapper: the graph mapper
        :param original_source_machine_vertex: the machine vertex that set
        off this application edge consideration
        :return: iterable of src machine vertices
        """

    @abstractmethod
    def get_pre_slice_for(self, machine_vertex):
        """ allows a application vertex to control the slices perceived by \
        out systems.

        :param machine_vertex: the machine vertex to hand slice for
        :return: the slice considered for this vertex
        """

    @abstractmethod
    def get_out_going_slices(self):
        """ allows a application vertex to control the set of slices for \
        outgoing application edges

        :return: list of Slices
        """
