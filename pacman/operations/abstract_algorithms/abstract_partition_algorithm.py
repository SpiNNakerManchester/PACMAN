from pacman.model.constraints.abstract_constraints\
    .abstract_partitioner_constraint import AbstractPartitionerConstraint
from pacman.utilities.progress_bar import ProgressBar

from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass
import logging

logger = logging.getLogger(__name__)


@add_metaclass(ABCMeta)
class AbstractPartitionAlgorithm(object):
    """ An abstract algorithm that can partition a partitionable_graph
    """

    def __init__(self):
        """
        """
        self._supported_constraints = list()

    @abstractmethod
    def partition(self, graph, machine):
        """ Partition a partitionable graph so that each subvertex will fit
            on a processor within the machine

        :param graph: The partitionable graph to partition
        :type graph:\
                    :py:class:`pacman.model.graph.partitionable_graph.PartitionableGraph`
        :param machine: The machine with respect to which to partition the \
                    partitionable_graph
        :type machine: :py:class:`spinn_machine.machine.Machine`
        :return: A partitioned graph of partitioned vertices and edges, and \
                    a graph mapper that maps between the paritioned vertices \
                    and the partitionable vertices
        :rtype:\
                    (:py:class:`pacman.model.partitioned_graph.partitioned_graph.PartitionedGraph`,\
                     :py:class:`pacman.model.graph_mapper.graph_mapper.GraphMapper`)
        :raise pacman.exceptions.PacmanPartitionException: If something \
                   goes wrong with the partitioning
        """
        pass

    @staticmethod
    def _generate_sub_edges(subgraph, graph_to_subgraph_mapper, graph):
        """ Generate the sub edges for the subvertices in the graph

        :param subgraph: the partitioned graph to work with
        :type subgraph:\
                    :py:class:`pacman.model.partitioned_graph.partitioned_graph.PartitionedGraph`
        :param graph_to_subgraph_mapper: the mapper between the \
                    partitionable graph and the partitioned graph
        :type graph_to_subgraph_mapper:\
                    :py:class:`pacman.model.graph_mapper.GraphMapper`
        :param graph: the partitionable graph to work with
        :type graph:\
                    :py:class:`pacman.model.graph.partitionable_graph.PartitionableGraph`
        """

        # start progress bar
        progress_bar = ProgressBar(len(subgraph.subvertices),
                                   "on partitioning the partitionable_graph's "
                                   "edges")

        # Partition edges according to vertex partitioning
        for src_sv in subgraph.subvertices:

            # For each out edge of the parent vertex...
            vertex = graph_to_subgraph_mapper.get_vertex_from_subvertex(src_sv)
            outgoing_partitions = \
                graph.outgoing_edges_partitions_from_vertex(vertex)
            for outgoing_partition_identifer in outgoing_partitions:
                out_edges = \
                    outgoing_partitions[outgoing_partition_identifer].edges
                for edge in out_edges:

                    # and create and store a new subedge for each postsubvertex
                    post_vertex = edge.post_vertex
                    post_subverts = (graph_to_subgraph_mapper
                                     .get_subvertices_from_vertex(post_vertex))
                    for dst_sv in post_subverts:
                        subedge = edge.create_subedge(src_sv, dst_sv)
                        subgraph.add_subedge(subedge,
                                             outgoing_partition_identifer)
                        graph_to_subgraph_mapper.add_partitioned_edge(
                            subedge, edge)
            progress_bar.update()
        progress_bar.end()

    @staticmethod
    def _get_remaining_constraints(vertex):
        """ Gets the rest of the constraints from a vertex after removing\
            partitioning constraints
        """
        constraints = list()
        for constraint in vertex.constraints:
            if not isinstance(constraint, AbstractPartitionerConstraint):
                constraints.append(constraint)
        return constraints
