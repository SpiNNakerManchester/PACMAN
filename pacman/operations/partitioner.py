from pacman import reports


class Partitioner:
    """ Used to partition a graph into a subgraph
    """

    def __init__(self, machine_time_step, no_machine_time_steps,
                 report_states, report_folder=None, partition_algorithm=None,
                 hostname=None):
        """
        :param partition_algorithm: A partitioning algorithm.  If not specified\
                    a default algorithm will be used
        :type partition_algorithm:\
                    :py:class:`pacman.operations.partition_algorithms.abstract_partition_algorithm.AbstractPartitionAlgorithm`
        :raise pacman.exceptions.PacmanInvalidParameterException: If\
                    partition_algorithm is not valid
        """
        self._report_folder = report_folder
        self.report_states = report_states
        self._hostname = hostname
        if partition_algorithm is None:
            pass
        else:
            self._partitoner_algorithum = \
                partition_algorithm(machine_time_step, no_machine_time_steps)

    def run(self, graph, machine):
        """ Execute the algorithm on the graph, and partition it to fit on\
            the cores of the machine
            
        :param graph: The graph to partition
        :type graph: :py:class:`pacman.model.graph.graph.Graph`
        :param machine: The machine with respect to which to partition the graph
        :type machine: :py:class:`spinn_machine.machine.Machine`
        :return: A subgraph of partitioned vertices and edges from the graph
        :rtype: :py:class:`pacman.model.subgraph.subgraph.Subgraph`
        :raise pacman.exceptions.PacmanPartitionException: If something\
                   goes wrong with the partitioning
        """
        subgraph, graph_to_subgraph_mapper = \
            self._partitoner_algorithum.partition(graph, machine)

        if (self.report_states is not None and
                self.report_states.partitioner_report):
            reports.partitioner_report(self._report_folder, subgraph, graph,
                                       graph_to_subgraph_mapper, self._hostname)

        return subgraph, graph_to_subgraph_mapper


