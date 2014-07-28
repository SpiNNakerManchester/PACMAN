from pacman.model.graph_subgraph_mapper.graph_subgraph_mapper import \
    GraphSubgraphMapper
from pacman.operations.partition_algorithms.abstract_partition_algorithm\
    import AbstractPartitionAlgorithm
from pacman.model.subgraph.subgraph import Subgraph
from pacman.model.subgraph.subvertex import Subvertex
from pacman.model.constraints.partitioner_maximum_size_constraint \
    import PartitionerMaximumSizeConstraint
from pacman import constants as pacman_constants


class PartitionAndPlacePartitioner(AbstractPartitionAlgorithm):
    """ An basic algorithm that can partition a graph based on atoms
    """

    def __init__(self, machine_time_step, runtime_in_machine_time_steps):
        """constructor to build a
        pacman.operations.partition_algorithms.partition_and_place_partitioner.PartitionAndPlacePartitioner
        :param machine_time_step: the length of tiem in ms for a timer tic
        :param runtime_in_machine_time_steps: the number of timer tics expected \
               to occur due to the runtime
        :type machine_time_step: int
        :type runtime_in_machine_time_steps: long
        :return: a new pacman.operations.partition_algorithms.abstract_partition_algorithm.AbstractPartitionAlgorithm
        :rtype: pacman.operations.partition_algorithms.abstract_partition_algorithm.AbstractPartitionAlgorithm
        :raises None: does not raise any known expection
        """
        AbstractPartitionAlgorithm.__init__(self, machine_time_step,
                                            runtime_in_machine_time_steps)

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

