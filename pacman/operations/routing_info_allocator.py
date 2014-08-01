import logging
from pacman.operations.routing_info_allocator_algorithms.\
    basic_routing_info_allocator import BasicRoutingInfoAllocator
from pacman.utilities import reports

logger = logging.getLogger(__name__)


class RoutingInfoAllocator:
    """ Used to obtain routing information from a placed subgraph
    """

    def __init__(self, machine, report_states, graph_to_sub_graph_mapper,
                 report_folder=None, hostname=None,
                 routing_info_allocator_algorithm=None):
        """
        :param routing_info_allocator_algorithm: The routing info allocator\
                    algorithm.  If not specified, a default algorithm will be\
                    used
        :type routing_info_allocator_algorithm:\
:py:class:`pacman.operations.routing_info_allocator_algorithms.abstract_routing_info_allocator_algorithm.AbstractRoutingInfoAllocatorAlgorithm`
        :raise pacman.exceptions.PacmanInvalidParameterException: If\
                    routing_info_allocator_algorithm is not valid
        """
        self._machine = machine
        self._report_folder = report_folder
        self.report_states = report_states
        self._hostname = hostname
        self._machine = machine
        self._graph_to_subgraph_mapper = graph_to_sub_graph_mapper
        self._routing_info_allocator_algorithm = \
            routing_info_allocator_algorithm

        #set up a default placer algorithum if none are specified
        if self._routing_info_allocator_algorithm is None:
            self._routing_info_allocator_algorithm = BasicRoutingInfoAllocator()
        else:
            self._routing_info_allocator_algorithm = \
                routing_info_allocator_algorithm()

    def run(self, subgraph, placements):
        """ Execute the algorithm on the subgraph
        
        :param subgraph: The subgraph to allocate the routing info for
        :type subgraph: :py:class:`pacman.model.subgraph.subgraph.Subgraph`
        :param placements: The placements of the subvertices
        :type placements: :py:class:`pacman.model.placements.placements.Placements`
        :return: The routing information
        :rtype: :py:class:`pacman.model.routing_info.routing_info.RoutingInfo`
        :raise pacman.exceptions.PacmanRouteInfoAllocationException: If\
                   something goes wrong with the allocation
        """
        #execute routing info generator
        routing_infos = \
            self._routing_info_allocator_algorithm.allocate_routing_info(
                subgraph, placements)

        #generate reports
        if (self.report_states is not None and
                self.report_states.routing_info_report):
            reports.routing_info_report(self._report_folder, self._hostname,
                                        subgraph, placements, routing_infos)

        return routing_infos
