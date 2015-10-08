"""
PartitionedGraph
"""

# pacman imports
from pacman.exceptions import PacmanInvalidParameterException
from pacman.exceptions import PacmanAlreadyExistsException
from pacman.utilities.utility_objs.ordered_set import OrderedSet
from pacman.utilities.utility_objs.outgoing_edge_partition import OutgoingEdgePartition

# general imports
import uuid


class PartitionedGraph(object):
    """ Represents a partitioning of a partitionable_graph
    """

    def __init__(self, label=None):
        """

        :param label: an identifier for the partitioned_graph
        :type label: str
        :raise pacman.exceptions.PacmanInvalidParameterException:
                    * If one of the subedges is not valid
                    * If one of the subvertices is not valid
        """
        self._label = label
        self._subvertices = OrderedSet()
        self._subedges = OrderedSet()

        self._outgoing_subedges = dict()
        self._incoming_subedges = dict()

    def add_subvertex(self, subvertex):
        """ Add a subvertex to this partitioned_graph

        :param subvertex: a subvertex to be added to the partitioned graph
        :type subvertex:\
                    :py:class:`pacman.model.partitioned_graph.partitioned_vertex.PartitionedVertex`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If the\
                    subvertex is not valid
        """
        if subvertex not in self._subvertices:
            self._subvertices.add(subvertex)
        else:
            raise PacmanAlreadyExistsException("PartitionedVertex",
                                               str(subvertex))
        self._outgoing_subedges[subvertex] = dict()
        self._incoming_subedges[subvertex] = list()

    def add_subvertices(self, subvertices):
        """ Add some subvertices to this partitioned_graph

        :param subvertices: an iterable of subvertices to add to this\
                    partitioned_graph
        :type subvertices: iterable of\
                    :py:class:`pacman.model.partitioned_graph.partitioned_vertex.PartitionedVertex`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If the\
                    subvertex is not valid
        """
        if subvertices is not None:
            for next_subvertex in subvertices:
                self.add_subvertex(next_subvertex)

    def add_subedge(self, subedge, partition_id=None):
        """ Add a subedge to this partitioned_graph

        :param subedge: a subedge to be added to the partitioned_graph
        :type subedge:\
                    :py:class:`pacman.model.partitioned_graph.abstract_partitioned_edge.AbstractPartitionedEdge`
        :param partition_id: the id for the outgoing partition that this edge
        is associated with
        :type partition_id: str
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If the\
                    subedge is not valid
        """
        if subedge in self._subedges:
            raise PacmanAlreadyExistsException(
                "FixedRoutePartitionableEdge", str(subedge))

        self._subedges.add(subedge)

        # if the partition id is none, make a unqiue one for storage
        if partition_id is None:
            partition_id = str(uuid.uuid4())

        if subedge.pre_subvertex in self._outgoing_subedges:
            # if this partition id not been seen before, add a new parittion
            if (partition_id not in
                    self._outgoing_subedges[subedge.pre_subvertex]):
                self._outgoing_subedges[subedge.pre_subvertex][partition_id] = \
                    OutgoingEdgePartition(partition_id)
            self._outgoing_subedges[subedge.pre_subvertex][partition_id]\
                .add_edge(subedge)
        else:
            raise PacmanInvalidParameterException(
                "FixedRoutePartitionableEdge pre_subvertex",
                str(subedge.pre_subvertex),
                " Must exist in the partitioned_graph")

        if subedge.post_subvertex in self._incoming_subedges:
            self._incoming_subedges[subedge.post_subvertex].append(subedge)
        else:
            raise PacmanInvalidParameterException(
                "FixedRoutePartitionableEdge post_subvertex",
                str(subedge.post_subvertex),
                " Must exist in the partitioned_graph")

    def add_subedges(self, subedges, partition_id=None):
        """ Add some subedges to this partitioned_graph

        :param subedges: an iterable of subedges to add to this\
                    partitioned_graph
        :type subedges: iterable of\
                    :py:class:`pacman.model.partitioned_graph.abstract_partitioned_edge.AbstractPartitionedEdge`
        :param partition_id: the id for the outgoing partition that this edge
        is associated with
        :type partition_id: str
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If the\
                    subedge is not valid
        """
        if subedges is not None:
            for next_subedge in subedges:
                self.add_subedge(next_subedge, partition_id)

    def outgoing_subedges_from_subvertex(
            self, subvertex, partition_identifer=None):
        """ Locate the subedges for which subvertex is the pre_subvertex.\
            Can return an empty collection

        :param subvertex: the subvertex for which to find the outgoing subedges
        :type subvertex:\
                    :py:class:`pacman.model.partitioned_graph.partitioned_vertex.PartitionedVertex`
        :param partition_identifer: the identifer for the partition that
        the edges being returned should associate with. If set to None, returns
        all edges from all parititons
        :type partition_identifer: string or None
        :return: an iterable of subedges which have subvertex as their\
                    pre_subvertex
        :rtype: iterable of\
                    :py:class:`pacman.model.partitioned_graph.abstract_partitioned_edge.AbstractPartitionedEdge`
        :raise None: does not raise any known exceptions
        """
        if partition_identifer is None:
            edges = list()
            for partition_identifer in self._outgoing_subedges[subvertex]:
                edges.extend(
                    self._outgoing_subedges[subvertex][partition_identifer]
                    .edges)
            return edges
        elif partition_identifer not in self._outgoing_subedges[subvertex]:
            return ()
        else:
            return self._outgoing_subedges[subvertex][partition_identifer].edges

    def outgoing_edges_partitions_from_vertex(self, sub_vertex):
        """ Locates all the outgoing edge partitions for a given vertex

        :param sub_vertex: the vertex for which the outgoing edge partitions are to
         be located for.
         :type sub_vertex: \
                    :py:class:`pacman.model.partitionable_graph.abstract_partitionable_vertex.AbstractPartitionableVertex`
        :return: iterable of\
                     :py:class:`pacman.utilities.outgoing_edge_partition.OutgoingEdgePartition`
                     or a empty list if none are avilable
        :raise None: does not raise any known exceptions
        """
        if sub_vertex in self._outgoing_subedges:
            return self._outgoing_subedges[sub_vertex]
        else:
            return ()

    def incoming_subedges_from_subvertex(self, subvertex):
        """ Locate the subedges for which subvertex is the post_subvertex.\
            Can return an empty collection.

        :param subvertex: the subvertex for which to find the incoming subedges
        :type subvertex:\
                    :py:class:`pacman.model.partitioned_graph.partitioned_vertex.PartitionedVertex`
        :return: an iterable of subedges which have subvertex as their\
                    post_subvertex
        :rtype: iterable of\
                    :py:class:`pacman.model.partitioned_graph.abstract_partitioned_edge.AbstractPartitionedEdge`
        :raise None: does not raise any known exceptions
        """
        if subvertex in self._incoming_subedges:
            return self._incoming_subedges[subvertex]
        return None

    def get_subvertex_with_label(self, label):
        """ Locates the subvertex which has the same label of the input

        :param label: the input label to search for.
        :return: the partitionedVertex or None if theres no vertex with this label
        """
        for vertex in self._subvertices:
            if vertex.label == label:
                return vertex
        return None

    def get_subedge_with_label(self, label, destination_sub_vertex):
        """ locates the subedge which has the same label of the input

        :param label: the input label to search for.
        :param destination_sub_vertex: the subvertex to which this edge goes to
        :return: the partitionedEdge or None if theres no vertex with this label
        """
        for subvertex in self._subvertices:
            for edge_partition_id in self._outgoing_subedges[subvertex]:
                vertex_and_partition_id = \
                    "{}:{}".format(subvertex.label, edge_partition_id)
                if vertex_and_partition_id == label:
                    edge_partition = \
                        self._outgoing_subedges[subvertex][edge_partition_id]
                    edges = edge_partition.edges

                    for edge in edges:
                        if edge.post_subvertex == destination_sub_vertex:
                            return edge
        return None

    def get_source_subvertex_with_label(self, label):
        """ locates the subedge which has the same label of the input

        :param label: the input label to search for.
        :return: the partitionedEdge or None if theres no vertex with this label
        """
        for subvertex in self._subvertices:
            for edge_partition_id in self._outgoing_subedges[subvertex]:
                vertex_and_partition_id = \
                    "{}:{}".format(subvertex.label, edge_partition_id)
                if vertex_and_partition_id == label:
                    edge_partition = \
                        self._outgoing_subedges[subvertex][edge_partition_id]
                    edge = edge_partition.edges[0]
                    return edge.pre_subvertex
        return None

    @property
    def subvertices(self):
        """ The subvertices of the partitioned_graph

        :return: an iterable of subvertices
        :rtype: iterable of\
                    :py:class:`pacman.model.partitioned_graph.partitioned_vertex.PartitionedVertex`
        """
        return self._subvertices

    @property
    def subedges(self):
        """ The subedges of the partitioned_graph

        :return: an iterable of subedges
        :rtype: iterable of\
                    :py:class:`pacman.model.partitioned_graph.abstract_partitioned_edge.AbstractPartitionedEdge`
        """
        return self._subedges

    @property
    def label(self):
        """ The label of the partitioned_graph

        :return: The label or None if there is no lable
        :rtype: str
        :raise None: Raises no known exceptions
        """
        return self._label
