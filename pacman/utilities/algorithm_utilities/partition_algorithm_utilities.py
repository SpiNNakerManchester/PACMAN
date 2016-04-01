"""
A collection of methods which support partitioning algorithms.
"""

import logging

from pacman.model.constraints.abstract_constraints\
    .abstract_partitioner_constraint import AbstractPartitionerConstraint
from spinn_machine.utilities.progress_bar import ProgressBar

logger = logging.getLogger(__name__)


def generate_sub_edges(subgraph, graph_to_subgraph_mapper, graph):
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
                               "Partitioning graph edges")

    # Partition edges according to vertex partitioning
    for src_sv in subgraph.subvertices:

        # For each out edge of the parent vertex...
        vertex = graph_to_subgraph_mapper.get_vertex_from_subvertex(src_sv)
        outgoing_partitions = \
            graph.outgoing_edges_partitions_from_vertex(vertex)
        for outgoing_partition_identifer in outgoing_partitions:
            partition = outgoing_partitions[outgoing_partition_identifer]
            out_edges = partition.edges
            partition_constraints = partition.constraints
            for edge in out_edges:

                # and create and store a new subedge for each post-subvertex
                post_vertex = edge.post_vertex
                post_subverts = (graph_to_subgraph_mapper
                                 .get_subvertices_from_vertex(post_vertex))
                for dst_sv in post_subverts:
                    subedge = edge.create_subedge(src_sv, dst_sv)
                    subgraph.add_subedge(subedge,
                                         outgoing_partition_identifer,
                                         partition_constraints)
                    graph_to_subgraph_mapper.add_partitioned_edge(
                        subedge, edge)
        progress_bar.update()
    progress_bar.end()


def get_remaining_constraints(vertex):
    """ Gets the rest of the constraints from a vertex after removing\
        partitioning constraints
    """
    constraints = list()
    for constraint in vertex.constraints:
        if not isinstance(constraint, AbstractPartitionerConstraint):
            constraints.append(constraint)
    return constraints
