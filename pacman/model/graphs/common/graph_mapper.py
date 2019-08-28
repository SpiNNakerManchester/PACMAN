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


class GraphMapper(object):
    """ A mapping between an Application Graph and a Machine Graph.
    """

    __slots__ = []

    @deprecated("Nothing in the GraphMapper class is useful any more")
    def __init__(self):
        pass

    @deprecated("just do application_vertex." +
                "remember_associated_machine_vertex(machine_vertex)")
    def add_vertex_mapping(
            self, machine_vertex, application_vertex):
        """ Add a mapping between application and machine vertices

        DEPRECATED

        :param machine_vertex: A vertex from a Machine Graph
        :param application_vertex: A vertex from an Application Graph
        :raise pacman.exceptions.PacmanValueError:\
            If atom selection is out of bounds.
        """
        application_vertex.remember_associated_machine_vertex(machine_vertex)

    @deprecated("just do \
        application_edge.remember_associated_machine_edge(machine_edge)")
    def add_edge_mapping(self, machine_edge, application_edge):
        """ Add a mapping between a machine edge and an application edge

        DEPRECATED

        :param machine_edge: An edge from a Machine Graph
        :param application_edge: An edge from an Application Graph
        """
        application_edge.remember_associated_machine_edge(machine_edge)

    @deprecated("just do application_vertex.machine_vertices")
    def get_machine_vertices(self, application_vertex):
        """ Get all machine vertices mapped to a given application vertex

        :param application_vertex: A vertex from an Application Graph
        :return: An iterable of machine vertices or None if none
        """
        return application_vertex.machine_vertices

    @deprecated("just do machine_vertex.index")
    def get_machine_vertex_index(self, machine_vertex):
        """ Get the index of a machine vertex within the list of such vertices\
            associated with an application vertex

        DEPRECATED

        :param machine_vertex: A vertex from a Machine Graph
        """
        return machine_vertex.index

    @deprecated("just do application_edge.machine_edges")
    def get_machine_edges(self, application_edge):
        """ Get all machine edges mapped to a given application edge

        DEPRECATED

        :param application_edge: An edge from an Application Graph
        :return: An iterable of machine edges or None if none
        """
        return application_edge.machine_edges

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

    @deprecated("just do machine_vertex.vertex_slice")
    def get_slice(self, machine_vertex):
        """ Get the slice mapped to a machine vertex

        DEPRECATED

        :param machine_vertex: A vertex in a Machine Graph
        :return: a slice object containing the low and high atom
        """
        return machine_vertex.vertex_slice

    @deprecated("just do application_vertex.vertex_slices")
    def get_slices(self, application_vertex):
        """ Get all the slices mapped to an application vertex

        DEPRECATED
        """
        return application_vertex.vertex_slices
