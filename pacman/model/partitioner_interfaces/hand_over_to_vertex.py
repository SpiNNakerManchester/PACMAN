from six import add_metaclass
from spinn_utilities.abstract_base import (
    AbstractBase, abstractmethod)


@add_metaclass(AbstractBase)
class HandOverToVertex(object):

    @abstractmethod
    def create_and_add_to_graphs_and_resources(
            self, resource_tracker, machine_graph, graph_mapper):
        """ hands over partitioning to the application vertex.

        :param resource_tracker: the resource tracker needed to be updated
        :param machine_graph: the machine graph to be updated
        :param graph_mapper: the graph mapper to be updated.
        :return: None
        """

    @abstractmethod
    def source_vertices_from_edge(self, edge):
        """ returns vertices for connecting this edge

        :param edge: edge to connect to sources
        :return: the iterable of vertices to be sources of this edge
        """

    @abstractmethod
    def destination_vertices_from_edge(self, edge):
        """ return vertices for connecting this edge

        :param edge: edge to connect to destinations
        :return: the iterable of vertices to be destinations of this edge.
        """
