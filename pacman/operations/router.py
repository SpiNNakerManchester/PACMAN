import logging
from pacman.utilities import reports
from pacman.operations.router_algorithms.basic_dijkstra_routing import BasicDijkstraRouting

logger = logging.getLogger(__name__)


class Router:
    """ Used to find routes through a machine
    """

    def __init__(self, report_states, partitionable_graph=None,
                 report_folder=None, hostname=None, router_algorithm=None,
                 graph_mappings=None):
        """
        :param router_algorithm: The router algorithm.  If not specified, a\
                    default algorithm will be used
        :type router_algorithm:\
:py:class:`pacman.operations.router_algorithms.abstract_router_algorithm.AbstractRouterAlgorithm`
        :param report_folder: the optimal param for the default location for \
        reports
        :param report_states: the data objects for what reports are needed
        :param partitionable_graph: the partitionable graph object (descirbes\
         the applciation problem in a high level)
        :param graph_mappings:
        :param hostname:
        :type report_folder:
        :type report_states:
        :type partitionable_graph:
        :type graph_mappings:
        :type hostname:
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If\
                    router_algorithm is not valid
        """
        self._report_folder = report_folder
        self.report_states = report_states
        self._hostname = hostname
        self._graph = partitionable_graph
        self._router_algorithm = router_algorithm
        self._graph_to_subgraph_mappings = graph_mappings

        #set up a default placer algorithm if none are specified
        if self._router_algorithm is None:
            self._router_algorithm = BasicDijkstraRouting()
        else:
            self._router_algorithm = router_algorithm()

    def run(self, routing_info_allocation, placements, machine,
            partitioned_graph):
        """ Execute the router algorithm, finding the routes through the\
            machine for the given placed subedges
            
        :param routing_info_allocation: The allocated routing information
        :type routing_info_allocation:\
                    :py:class:`pacman.model.routing_info.routing_info.RoutingInfo`
        :param placements: The placements of the subedges
        :type placements:\
                    :py:class:`pacman.model.placements.placements.Placements`
        :param machine: The machine through which the routes are to be found
        :type machine: :py:class:`spinn_machine.machine.Machine`
        :param partitioned_graph: the partitioned graph object (sub graph in \
        old naming convention)
        :type partitioned_graph:
    pacman.model.partioned_graph.partitioned_graph.PartitionedGraph
        :return: The discovered routes 
        :rtype: :py:class:`pacman.model.routing_tables.multicast_routing_tables.MulticastRoutingTables`
        :raise pacman.exceptions.PacmanRoutingException: If something\
                   goes wrong with the routing
        """
        routing_tables = \
            self._router_algorithm.route(routing_info_allocation, placements,
                                         machine, partitioned_graph)

        #execute reports if needed
        if self.report_states is not None and self.report_states.router_report:
            reports.router_reports(
                graph=self._graph, hostname=self._hostname,
                graph_to_sub_graph_mapper=self._graph_to_subgraph_mappings,
                placements=placements, report_folder=self._report_folder,
                include_dat_based=self.report_states.router_dat_based_report,
                routing_tables=routing_tables, 
                routing_info=routing_info_allocation,
                machine=machine)

        return routing_tables