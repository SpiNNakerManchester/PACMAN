from pacman.operations.placer_algorithms.basic_placer import BasicPlacer
from pacman.utilities import reports

import logging

logger = logging.getLogger(__name__)


class Placer:
    """ Used to place the subvertices of a subgraph on to specific cores of\
        a machine
    """

    def __init__(self, machine, report_states, report_folder=None,
                 hostname=None, placer_algorithm=None, graph=None):
        """
        :param placer_algorithm: The placer algorithm.  If not specified, a\
                    default algorithm will be used
        :type placer_algorithm:\
                    :py:class:`pacman.operations.placer_algorithms.abstract_placer_algorithm.AbstractPlacerAlgorithm`
        :param machine: the machine object
        :type machine: a spinnmachine.machine.Machine object
        :raise pacman.exceptions.PacmanInvalidParameterException: If\
                    placer_algorithm is not valid
        """
        self._report_folder = report_folder
        self.report_states = report_states
        self._hostname = hostname
        self._machine = machine
        self._graph = graph
        self._placer_alogrithum = placer_algorithm

        #set up a default placer algorithum if none are specified
        if self._placer_alogrithum is None:
            self._placer_alogrithum = BasicPlacer(self._machine, self._graph)
        else:
            self._placer_alogrithum = placer_algorithm(self._machine,
                                                       self._graph)

    def run(self, subgraph, graph_to_subgraph_mapper):
        """ Execute the algorithm on the subgraph and place it on the machine
        
        :param subgraph: The subgraph to place
        :type subgraph: :py:class:`pacman.model.subgraph.subgraph.Subgraph`
        :return: A set of placements
        :rtype: :py:class:`pacman.model.placements.placements.Placements`
        :raise pacman.exceptions.PacmanPlaceException: If something\
                   goes wrong with the placement
        """
        placements = \
            self._placer_alogrithum.place(subgraph, graph_to_subgraph_mapper)

        #execute reports if needed
        if (self.report_states is not None and
                self.report_states.placer_report):
            reports.placer_report(
                graph=self._graph, hostname=self._hostname,
                graph_to_subgraph_mapper=graph_to_subgraph_mapper,
                machine=self._machine, placements=placements,
                report_folder=self._report_folder)

        return placements

