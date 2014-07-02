class Placer:
    """ Used to place the subvertices of a subgraph on to specific cores of\
        a machine
    """

    def __init__(self, placer_algorithm=None):
        """
        :param placer_algorithm: The placer algorithm.  If not specified, a\
                    default algorithm will be used
        :type placer_algorithm:\
                    :py:class:`pacman.operations.placer_algorithms.abstract_placer_algorithm.AbstractPlacerAlgorithm`
        :raise pacman.exceptions.PacmanInvalidParameterException: If\
                    placer_algorithm is not valid
        """
        pass

    def run(self, subgraph, machine):
        """ Execute the algorithm on the subgraph and place it on the machine
        
        :param subgraph: The subgraph to place
        :type subgraph: :py:class:`pacman.model.subgraph.subgraph.Subgraph`
        :param machine: The machine on which to place the graph
        :type machine: :py:class:`pacman.model.machine.machine.Machine`
        :return: A set of placements
        :rtype: :py:class:`pacman.model.placements.placements.Placements`
        :raise pacman.exceptions.PacmanPlaceException: If something\
                   goes wrong with the placement
        """
        pass
