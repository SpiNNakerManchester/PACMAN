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

from deprecated import deprecated
from spinn_utilities.ordered_default_dict import DefaultOrderedDict
from spinn_utilities.ordered_set import OrderedSet
from pacman.exceptions import PacmanValueError


class GraphMapper(object):
    """ A mapping between an Application Graph and a Machine Graph.
    """

    __slots__ = [
        # dict of application vertex -> set of machine vertices
        "_machine_vertices_by_application_vertex",

        # dict of application edge -> set of machine edges
        "_machine_edges_by_application_edge",

        # dict of machine vertex -> index of vertex in list of vertices from
        #                           the same application vertex
        "_index_by_machine_vertex",

        # dict of machine_vertex -> slice of atoms from application vertex
        "_slice_by_machine_vertex",

        # dict of application vertex -> list of slices of application vertex
        "_slices_by_application_vertex"
    ]

    def __init__(self):
        self._machine_vertices_by_application_vertex = \
            DefaultOrderedDict(OrderedSet)
        self._machine_edges_by_application_edge = \
            DefaultOrderedDict(OrderedSet)

        self._index_by_machine_vertex = dict()
        self._slice_by_machine_vertex = dict()
        self._slices_by_application_vertex = DefaultOrderedDict(list)

    def add_vertex_mapping(
            self, machine_vertex, vertex_slice, application_vertex):
        """ Add a mapping between application and machine vertices

        :param machine_vertex: A vertex from a Machine Graph
        :param vertex_slice:\
            The range of atoms from the application vertex that is going to be\
            in the machine_vertex
        :type vertex_slice: :py:class:`pacman.model.graphs.common.Slice`
        :param application_vertex: A vertex from an Application Graph
        :raise pacman.exceptions.PacmanValueError:\
            If atom selection is out of bounds.
        """
        if vertex_slice.hi_atom >= application_vertex.n_atoms:
            raise PacmanValueError(
                "hi_atom {:d} >= maximum {:d}".format(
                    vertex_slice.hi_atom, application_vertex.n_atoms))

        machine_vertices = self._machine_vertices_by_application_vertex[
            application_vertex]
        self._index_by_machine_vertex[machine_vertex] = len(machine_vertices)
        machine_vertices.add(machine_vertex)
        self._slice_by_machine_vertex[machine_vertex] = vertex_slice
        self._slices_by_application_vertex[application_vertex].append(
            vertex_slice)

    def add_edge_mapping(self, machine_edge, application_edge):
        """ Add a mapping between a machine edge and an application edge

        :param machine_edge: An edge from a Machine Graph
        :param application_edge: An edge from an Application Graph
        """
        self._machine_edges_by_application_edge[application_edge].add(
            machine_edge)

    def get_machine_vertices(self, application_vertex):
        """ Get all machine vertices mapped to a given application vertex

        :param application_vertex: A vertex from an Application Graph
        :return: An iterable of machine vertices or None if none
        """
        return self._machine_vertices_by_application_vertex.get(
            application_vertex, None)

    def get_machine_vertex_index(self, machine_vertex):
        """ Get the index of a machine vertex within the list of such vertices\
            associated with an application vertex
        """
        return self._index_by_machine_vertex[machine_vertex]

    def get_machine_edges(self, application_edge):
        """ Get all machine edges mapped to a given application edge

        :param application_edge: An edge from an Application Graph
        :return: An iterable of machine edges or None if none
        """
        return self._machine_edges_by_application_edge.get(
            application_edge, None)

    @deprecated("just do machine_vertex.app_vertex")
    def get_application_vertex(self, machine_vertex):
        """ Get the application vertex mapped to a machine vertex

        DEPRECATED

        :param machine_vertex: A vertex from a Machine Graph
        :return: an application vertex, or None if none
        """
        return machine_vertex.app_vertex

    @deprecated("just do machine_edge.app_edge")
    def get_application_edge(self, machine_edge):
        """ Get the application edge mapped to a machine edge

        DEPRECATED

        :param machine_edge: An edge from a Machine Graph
        :return: A machine edge, or None if none
        """
        return machine_edge.app_edge

    def get_slice(self, machine_vertex):
        """ Get the slice mapped to a machine vertex

        :param machine_vertex: A vertex in a Machine Graph
        :return:\
            a slice object containing the low and high atom or None if none
        """
        return self._slice_by_machine_vertex.get(machine_vertex, None)

    def get_slices(self, application_vertex):
        """ Get all the slices mapped to an application vertex
        """
        return self._slices_by_application_vertex.get(application_vertex, None)
