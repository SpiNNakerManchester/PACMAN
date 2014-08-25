from pacman.operations.placer_algorithms.basic_placer import BasicPlacer
from pacman.utilities import reports

import logging

logger = logging.getLogger(__name__)


class Placer:
    """ Used to place the subvertices of a partitioned_graph on to
    specific cores of a machine
    """

    def __init__(self, machine, report_states, report_folder=None,
                 hostname=None, placer_algorithm=None, partitonable_graph=None):
        """
        :param placer_algorithm: The placer algorithm.  If not specified, a\
                    default algorithm will be used
        :param machine: the machine object
        :param report_folder: the folder where reports are stored
        :param report_states: the states of pacman based report values
        :param hostname: the hostname of the machine
        :param partitonable_graph: the partitionable_graph object of the\
        application problem
        :type report_states: pacman.utility.report_states.ReportStates
        :type report_folder: str
        :type hostname: int
        :type partitonable_graph:
        :py:class:`pacman.model.partitionable_graph.partitionable_graph.Graph object`
        :type placer_algorithm:\
:py:class:`pacman.operations.placer_algorithms.abstract_placer_algorithm.AbstractPlacerAlgorithm`
        :type machine: a spinnmachine.machine.Machine object
        :raise pacman.exceptions.PacmanInvalidParameterException: If\
                    placer_algorithm is not valid
        """
        self._report_folder = report_folder
        self.report_states = report_states
        self._hostname = hostname
        self._machine = machine
        self._partitonable_graph = partitonable_graph
        self._placer_algorithm = placer_algorithm

        #set up a default placer algorithm if none are specified
        if self._placer_algorithm is None:
            self._placer_algorithm = BasicPlacer(self._machine,
                                                 self._partitonable_graph)
        else:
            self._placer_algorithm = placer_algorithm(self._machine,
                                                      self._partitonable_graph)

    def run(self, subgraph, graph_mapper):
        """ Execute the algorithm on the partitioned_graph and place it on the machine
        
        :param subgraph: The partitioned_graph to place
        :type subgraph: :py:class:`pacman.model.subgraph.subgraph.Subgraph`
        :return: A set of placements
        :rtype: :py:class:`pacman.model.placements.placements.Placements`
        :raise pacman.exceptions.PacmanPlaceException: If something\
                   goes wrong with the placement
        """
        placements = \
            self._placer_algorithm.place(subgraph, graph_mapper)

        #execute reports if needed
        if (self.report_states is not None and
                self.report_states.placer_report):
            reports.placer_reports(
                graph=self._partitonable_graph, hostname=self._hostname,
                graph_mapper=graph_mapper, machine=self._machine,
                placements=placements, report_folder=self._report_folder)

        return placements

