from six import add_metaclass
from spinn_utilities.abstract_base import (
    AbstractBase, abstractmethod)


@add_metaclass(AbstractBase)
class AbstractControlsSourceOfEdges(object):
    def __init__(self):
        pass

    @abstractmethod
    def get_destinations_for_edge_from(self, destination, partition_id):
        """ allows a vertex to decide which of its internal machine vertices 
        sends a given machine edge

        :param destination: the dest of the edge
        :param partition_id: the outgoing partition id
        :return: iterable of src machine vertices
        """