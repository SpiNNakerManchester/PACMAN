from pacman.model.graph_subgraph_mapper.graph_subgraph_mapper import \
    GraphSubgraphMapper
from pacman.operations.partition_algorithms.abstract_partition_algorithm\
    import AbstractPartitionAlgorithm
from pacman.model.subgraph.subgraph import Subgraph
from pacman.model.subgraph.subvertex import Subvertex
from pacman.model.constraints.partitioner_maximum_size_constraint \
    import PartitionerMaximumSizeConstraint
from pacman import constants as pacman_constants
from pacman.progress_bar import ProgressBar


class BasicPartitioner(AbstractPartitionAlgorithm):
    """ An basic algorithm that can partition a graph based on atoms
    """

    def __init__(self, machine_time_step, runtime_in_machine_time_steps):
        """constructor to build a pacman.operations.partition_algorithms.basic_partitioner.BasicPartitioner

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
        self._supported_constrants.append(PartitionerMaximumSizeConstraint)

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
        self._check_can_support_constraints(graph)
        #start progress bar
        progress_bar = ProgressBar(len(graph.vertices))
        vertices = graph.vertices
        subgraph = Subgraph(label="subgraph for graph {}".format(graph.label))
        graph_to_subgraph_mapper = GraphSubgraphMapper()
        # Partition one vertex at a time
        for vertex in vertices:
            # Compute atoms per core from resource availability
            partition_object = vertex.get_partition_data_object()
            requirements, partition_object = \
                vertex.get_resources_for_atoms(
                    0, 1, self._runtime_in_machine_time_steps,
                    self._machine_time_step, partition_object)

            #locate max sdram avilable. SDRAM is the only one thats changeable
            #during partitioning, as dtcm and cpu cycles are bespoke to a
            #processor.

            max_sdram_usage = \
                self._get_maximum_resources_per_processor(vertex.constraints,
                                                          machine)
            apc_sd = max_sdram_usage / requirements.sdram
            apc_dt = pacman_constants.DTCM_AVAILABLE / requirements.dtcm
            apc_cp = pacman_constants.CPU_AVAILABLE / requirements.cpu
            max_atom_values = [apc_sd, apc_dt, apc_cp]

            # Check for any model-specific constraint on atoms per core and use
            # it, if it's more constraining than the current apc value:
            model_name = vertex.model_name

            max_atoms_constraints = \
                self._locate_max_atom_constrants(vertex.constraints)
            for max_atom_constrant in max_atoms_constraints:
                max_atom_values.append(max_atom_constrant.size)

            apc = min(max_atom_values)

            # Partition into subvertices
            counted = 0
            while counted < vertex.n_atoms:
                # Determine subvertex size
                remaining = vertex.n_atoms - counted
                if remaining > apc:
                    alloc = apc
                else:
                    alloc = remaining
                # Create and store new subvertex, and increment elements
                #  counted
                label = "subvert with atoms {} to {} for vertex {}"\
                    .format(counted, counted + alloc - 1, vertex.label)
                subvert = Subvertex(counted, counted + alloc - 1,
                                    label=label)
                subgraph.add_subvertex(subvert)
                graph_to_subgraph_mapper.add_subvertex(subvert, vertex)
                counted = counted + alloc
            #update and end progress bars as needed
            progress_bar.update()
        progress_bar.end()

        #start progress bar
        progress_bar = ProgressBar(len(subgraph.subvertices))

        # Partition edges according to vertex partitioning
        for src_sv in subgraph.subvertices:
            # For each out edge of the parent vertex...
            vertex = graph_to_subgraph_mapper._vertex_from_subvertex(src_sv)
            for edge in vertex.out_edges:
                # ... and create and store a new subedge for each postsubvertex
                post_vertex = edge.post_vertex
                post_subverts = \
                    graph_to_subgraph_mapper\
                    ._subvertices_from_vertex(post_vertex)
                for dst_sv in post_subverts:
                    subedge = edge.create_subedge(src_sv, dst_sv)
                    subgraph.add_subedge(subedge)
            progress_bar.update()
        progress_bar.end()


        return subgraph