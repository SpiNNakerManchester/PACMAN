class Partitioner:
    """ Used to partition a graph into a subgraph
    """

    def __init__(self, partition_algorithm=None):
        """
        :param partition_algorithm: A partitioning algorithm.  If not specified\
                    a default algorithm will be used
        :type partition_algorithm:\
                    :py:class:`pacman.operations.partition_algorithms.abstract_partition_algorithm.AbstractPartitionAlgorithm`
        :raise pacman.exceptions.PacmanInvalidParameterException: If\
                    partition_algorithm is not valid
        """
        pass

    def run(self, graph, machine):
        """ Execute the algorithm on the graph, and partition it to fit on\
            the cores of the machine
            
        :param graph: The graph to partition
        :type graph: :py:class:`pacman.model.graph.graph.Graph`
        :param machine: The machine with respect to which to partition the graph
        :type machine: :py:class:`pacman.model.machine.machine.Machine`
        :return: A subgraph of partitioned vertices and edges from the graph
        :rtype: :py:class:`pacman.model.subgraph.subgraph.Subgraph`
        :raise pacman.exceptions.PacmanPartitionException: If something\
                   goes wrong with the partitioning
        """
        pass
