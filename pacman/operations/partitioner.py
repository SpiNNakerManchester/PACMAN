from pacman.operations.partition_algorithms.abstract_partition_algorithm \
    import AbstractPartitionAlgorithm
from pacman.operations.partition_algorithms.basic_partitioner \
    import BasicPartitioner
from pacman.utilities import reports
from pacman import exceptions

import logging

logger = logging.getLogger(__name__)


class Partitioner:
    """ Used to partition a partitionable_graph into a partitioned_graph
    """

    def __init__(self, machine_time_step, no_machine_time_steps,
                 report_states, partition_algorithm, machine,
                 placer_algorithm=None, report_folder=None, hostname=None):
        """
        :param partition_algorithm: A partitioning algorithm.  If not specified\
                    a default algorithm will be used
        :param machine_time_step: the time step fo the machine to which this \
        application is being compiled to
        :param no_machine_time_steps: The number of machine time steps that \
        this application will run for
        :param report_states: a holder class for what reports are needed to be \
        enabled
        :param placer_algorithm: which placer algorithm is going to be used by\
        algorithms which require a placement algorithm during partitioning
        :param report_folder: the file path to which where reports are to be \
        placed
        :param hostname: the hostname of the machine to which this application\
         is being compiled
        :type partition_algorithm:\
                    :py:class:`pacman.operations.partition_algorithms.abstract_partition_algorithm.AbstractPartitionAlgorithm`
        :type machine_time_step: int
        :type no_machine_time_steps: int
        :type report_states: pacman.utilities.report_states.ReportStates
        :type placer_algorithm: implementation of pacman.operations.placer_algorithms.AbstractPlacementAlgorithm
        :type report_folder: str
        :type hostname: str
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If\
                    partition_algorithm is not valid
        """
        self._report_folder = report_folder
        self.report_states = report_states
        self._hostname = hostname
        self._optimal_placer_alogrithm = placer_algorithm
        self._machine = machine

        #set up partitioner algorithm
        if partition_algorithm is None:
            self._partitioner_algorithm = \
                BasicPartitioner(machine_time_step, no_machine_time_steps)
        else:
            if not partition_algorithm in \
                    AbstractPartitionAlgorithm.__subclasses__():
                raise exceptions.PacmanInvalidParameterException(
                    "The given partitioning algorithm object is not a "
                    "recongised partitioning algorithm", partition_algorithm,
                    partition_algorithm)

            self._partitioner_algorithm = \
                partition_algorithm(machine_time_step, no_machine_time_steps)

    def run(self, partitionable_graph):
        """ Execute the algorithm on the partitionable_graph, and partition \
        it to fit on the cores of the machine
            
        :param partitionable_graph: The partitionable_graph to partition
        :type partitionable_graph:
        :py:class:`pacman.model.graph.partitionable_graph.PartitionableGraph`
        :return: A partitioned_graph of partitioned vertices and edges from \
        the partitionable_graph
        and a partitionable_graph to partitioned_graph mapper object which \
        links the partitionable_graph to the partitioned_graph objects
        :rtype: :py:class:`pacman.model.subgraph.subgraph.Subgraph`
        :raise pacman.exceptions.PacmanPartitionException: If something\
                   goes wrong with the partitioning
        """
        #if the algorithm requires a placer, set up this placer param
        if hasattr(self._partitioner_algorithm, "set_placer_algorithm"):
            self._partitioner_algorithm.set_placer_algorithm(
                self._optimal_placer_alogrithm, self._machine,
                partitionable_graph)

        subgraph, graph_mapper = \
            self._partitioner_algorithm.partition(partitionable_graph,
                                                  self._machine)

        if (self.report_states is not None and
                self.report_states.partitioner_report):
            reports.partitioner_reports(
                self._report_folder, self._hostname, partitionable_graph,
                graph_mapper)

        return subgraph, graph_mapper
