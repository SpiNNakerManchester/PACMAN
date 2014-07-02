class Pruner:
    """ Used to prune the subgraph, removing unused edges
    """

    def __init__(self, pruner_algorithm=None):
        """
        :param pruner_algorithm: The pruner algorithm.  If not specified, a\
                    default algorithm will be used
        :type pruner_algorithm:\
                    :py:class:`pacman.operations.pruner_algorithms.abstract_pruner_algorithm.AbstractPrunerAlgorithm`
        :raise pacman.exceptions.PacmanInvalidParameterException: If\
                    pruner_algorithm is not valid
        """
        pass

    def run(self, subgraph):
        """ Execute the algorithm on the subgraph
        
        :param subgraph: The subgraph to prune
        :type subgraph: :py:class:`pacman.model.subgraph.subgraph.Subgraph`
        :return: The items which are prunable
        :rtype: :py:class:`pacman.model.prunables.prunables.Prunables`
        :raise pacman.exceptions.PacmanPruneException: If something\
                   goes wrong with the pruning
        """
        pass
