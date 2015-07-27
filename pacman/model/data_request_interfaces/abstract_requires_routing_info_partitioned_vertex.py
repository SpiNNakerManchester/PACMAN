from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod

@add_metaclass(ABCMeta)
class RequiresRoutingInfoPartitionedVertex(object):
    """
    class which can be inhirttied from, which will then force the key
    allocator to inform the vertex of itw keys when decided upon.
    """

    def __init__(self):
        pass

    @abstractmethod
    def set_routing_infos(self, subedge_routing_infos):
        """
        abstract method to force systems which need to adjust their code when
        keys are allocated.
        :param subedge_routing_infos: a iterable of subedge_routing_info
        :return: none
        """