from six import add_metaclass
from spinn_utilities.abstract_base import (
    AbstractBase, abstractmethod)


@add_metaclass(AbstractBase)
class AbstractControlsDestinationOfEdges(object):

    def __init__(self):
        pass

    @abstractmethod
    def get_destinations_for_edge_from(
            self, app_edge, partition_id, graph_mapper,
            original_source_machine_vertex):
        """ allows a vertex to decide which of its internal machine vertices 
        take a given machine edge
        
        :param app_edge: the application edge
        :param partition_id: the outgoing partition id
        :param graph_mapper: the graph mapper
        :param original_source_machine_vertex: the machine vertex that set 
        off this application edge consideration
        :return: iterable of destination machine vertices
        """

    @abstractmethod
    def get_post_slice_for(self, machine_vertex):
        """ allows a application vertex to control the slices perceived by 
        out systems.

        :param machine_vertex: the machine vertex to hand slice for
        :return: the slice considered for this vertex
        """

    @abstractmethod
    def get_in_coming_slices(self):
        """ allows a application vertex to control the set of slices for 
        incoming application edges

        :return: 
        """