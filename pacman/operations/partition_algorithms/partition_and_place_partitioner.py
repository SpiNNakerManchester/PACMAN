from pacman.operations.partition_algorithms.abstract_partition_algorithm\
    import AbstractPartitionAlgorithm


class PartitionAndPlacePartitioner(AbstractPartitionAlgorithm):
    """ An basic algorithm that can partition a graph based on atoms
    """

    def __init__(self):
        """constructor to build a
        pacman.operations.partition_algorithms.partition_and_place_partitioner.PartitionAndPlacePartitioner
        <params to fill in when built>
        """
        pass

    #inherited from AbstractPartitionAlgorithm
    def partition(self, graph, machine):
        """ Partition a graph so that each subvertex will fit on a processor\
            within the machine

        :param graph: The graph to partition
        :type graph: :py:class:`pacman.model.graph.graph.Graph`
        :param machine: The machine with respect to which to partition the graph
        :type machine: :py:class:`spinn_machine.machine.Machine`
        :return: A subgraph of partitioned vertices and edges from the graph
        :rtype: :py:class:`pacman.model.subgraph.subgraph.Subgraph`
        :raise pacman.exceptions.PacmanPartitionException: If something\
                   goes wrong with the partitioning
        """
        pass

