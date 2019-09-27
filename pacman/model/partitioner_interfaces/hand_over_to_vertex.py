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
