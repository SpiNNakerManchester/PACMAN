from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass


@add_metaclass(ABCMeta)
class AbstractRoutingInfoAllocatorAlgorithm(object):
    """ An abstract algorithm that can produce routing keys and masks for\
        subedges in a partitioned_graph
    """

    def __init__(self):
        """constructor for a abstract routing info allocator\
         CANNOT BE INSTANITAED DIRECTLY
        """
        self._supported_constraints = list()
        self._used_masks = dict()
        self._subvert_to_key_mapper = dict()

    @abstractmethod
    def allocate_routing_info(self, subgraph, placements):
        """ Allocates routing information to the subedges in a\
            partitioned_graph

        :param subgraph: The partitioned_graph to allocate the routing info for
        :type subgraph: :py:class:`pacman.model.subgraph.subgraph.Subgraph`
        :param placements: The placements of the subvertices
        :type placements:\
                    :py:class:`pacman.model.placements.placements.Placements`
        :return: The routing information
        :rtype: :py:class:`pacman.model.routing_info.routing_info.RoutingInfo`
        :raise pacman.exceptions.PacmanRouteInfoAllocationException: If\
                   something goes wrong with the allocation
        """

    @abstractmethod
    def _generate_keys_with_atom_id(self, vertex_slice, vertex, placement,
                                    subedge):
        """ generates all keys required for a subvertex placed on a processor
        based on the number of atoms in the subvertex

        :param vertex_slice: the slice representing the subvertex
        :param placement: the placement of the subvertex
        :param vertex: the vertex this subvertex exists from
        :param subedge: the subedge associated with this key
        :return: a list of atom based keys.
        """
