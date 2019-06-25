from six import add_metaclass
from spinn_utilities.abstract_base import (
    AbstractBase, abstractmethod)


@add_metaclass(AbstractBase)
class AbstractControlsDestinationOfEdges(object):

    def __init__(self):
        pass

    @abstractmethod
    def get_destinations_for_edge_from(self, source_vertex, partition_id):
        """ allows a vertex to decide which of its internal machine vertices 
        take a given machine edge
        
        :param source_vertex: the src of the edge
        :param partition_id: the outgoing partition id
        :return: iterable of destination machine vertices
        """