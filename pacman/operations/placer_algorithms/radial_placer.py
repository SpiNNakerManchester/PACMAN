from pacman.operations.placer_algorithms.abstract_placer_algorithm import\
    AbstractPlacerAlgorithm

import logging

logger = logging.getLogger(__name__)


class RadialPlacer(AbstractPlacerAlgorithm):
    """ An radial algorithm that can place a subgraph onto a machine based off a
    circle out behaviour from a ethernet at 0 0
    """

    def __init__(self, machine):
        """constructor to build a
        pacman.operations.placer_algorithms.RadialPlacer.RadialPlacer
        :param machine: The machine on which to place the graph
        :type machine: :py:class:`spinn_machine.machine.Machine`
        """
        AbstractPlacerAlgorithm.__init__(self, machine)

    def place(self, subgraph, graph_to_subgraph_mapper):
        """ Place a subgraph so that each subvertex is placed on a core

        :param subgraph: The subgraph to place
        :type subgraph: :py:class:`pacman.model.subgraph.subgraph.Subgraph`
        :param graph_to_subgraph_mapper: the mappings between graph and subgraph
        :type graph_to_subgraph_mapper:
        pacman.model.graph_subgraph_mapper.graph_subgraph_mapper.GraphSubgraphMapper
        :return: A set of placements
        :rtype: :py:class:`pacman.model.placements.placements.Placements`
        :raise pacman.exceptions.PacmanPlaceException: If something\
                   goes wrong with the placement
        """
        pass