from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass
from pacman.model.routing_tables.multicast_routing_tables import \
    MulticastRoutingTables


@add_metaclass(ABCMeta)
class AbstractFixedRouteRouterAlgorithm(object):
    """ An abstract algorithm that can find routes for subedges between\
        subvertices in a partitioned_graph that have been placed on a machine
    """

    def __init__(self):
        """constructor for abstract routing algorithms"""
        self._routing_tables = MulticastRoutingTables()
    
    @abstractmethod
    def route(self, routing_info_allocation, placements, machine, sub_graph):
        """ Find routes between the subedges with the allocated information,
            placed in the given places
            
        :param routing_info_allocation: The allocated routing information
        :type routing_info_allocation:\
                    :py:class:`pacman.model.routing_info.routing_info.RoutingInfo`
        :param placements: The placements of the subedges
        :type placements:\
                    :py:class:`pacman.model.placements.placements.Placements`
        :param machine: The machine through which the routes are to be found
        :type machine: :py:class:`spinn_machine.machine.Machine`
        :param sub_graph: the partitioned_graph object
        :type sub_graph: pacman.partitioned_graph.partitioned_graph.Subgraph
        :return: The discovered routes 
        :rtype: :py:class:`pacman.model.routing_tables.multicast_routing_tables.MulticastRoutingTables`
        :raise pacman.exceptions.PacmanRoutingException: If something\
                   goes wrong with the routing
        """
        pass
