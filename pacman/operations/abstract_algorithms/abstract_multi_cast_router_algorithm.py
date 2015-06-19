from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass
from pacman.model.routing_paths.multicast_routing_paths import \
    MulticastRoutingPaths


@add_metaclass(ABCMeta)
class AbstractMultiCastRouterAlgorithm(object):
    """ An abstract algorithm that can find routes for multicast subedges\
        between subvertices in a partitioned_graph that have been placed on a\
        machine
    """

    def __init__(self):
        self._routing_paths = MulticastRoutingPaths()

    @abstractmethod
    def route(self, placements, machine, sub_graph):
        """ Find routes between the subedges with the allocated information,
            placed in the given places

        :param placements: The placements of the subedges
        :type placements:\
                    :py:class:`pacman.model.placements.placements.Placements`
        :param machine: The machine through which the routes are to be found
        :type machine: :py:class:`spinn_machine.machine.Machine`
        :param sub_graph: the partitioned_graph object
        :type sub_graph:\
                    :py:class:`pacman.partitioned_graph.partitioned_graph.Subgraph`
        :return: The discovered routes
        :rtype:\
                    :py:class:`pacman.model.routing_tables.multicast_routing_tables.MulticastRoutingTables`
        :raise pacman.exceptions.PacmanRoutingException: If something\
                   goes wrong with the routing
        """
        pass
