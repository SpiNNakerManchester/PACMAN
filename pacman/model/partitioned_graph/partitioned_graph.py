# pacman imports
from pacman.exceptions import PacmanInvalidParameterException
from pacman.exceptions import PacmanAlreadyExistsException
from pacman.utilities.utility_objs.ordered_set import OrderedSet
from pacman.utilities.utility_objs.outgoing_edge_partition import \
    OutgoingEdgePartition

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

        self._subedge_to_partition = dict()

        self._id_to_object_mapping = dict()

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
        # update id mapping
        self._id_to_object_mapping[str(id(subvertex))] = subvertex

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

    def add_subedge(self, subedge, partition_id=None,
                    partition_constraints=None):
        """ Add a subedge to this partitioned_graph

        :param subedge: a subedge to be added to the partitioned_graph
        :type subedge:\
                    :py:class:`pacman.model.partitioned_graph.abstract_partitioned_edge.AbstractPartitionedEdge`
        :param partition_id: the id for the outgoing partition that this edge\
                    is associated with
        :type partition_id: str
        :param partition_constraints: list of constraints to put onto the
        partition
        :type partition_constraints: iterable of
                :py:class:`pacman.model.constraints.abstract_constraints.abstract_constraint.AbstractConstraint`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If the\
                    subedge is not valid
        """
        if subedge in self._subedges:
            raise PacmanAlreadyExistsException(
                "FixedRoutePartitionableEdge", str(subedge))

        self._subedges.add(subedge)

        # if the partition id is none, make a unique one for storage
        if partition_id is None:
            partition_id = str(uuid.uuid4())

        if subedge.pre_subvertex in self._outgoing_subedges:
            # if this partition id not been seen before, add a new partition
            if (partition_id not in
                    self._outgoing_subedges[subedge.pre_subvertex]):
                self._outgoing_subedges[subedge.pre_subvertex][partition_id] =\
                    OutgoingEdgePartition(partition_id, partition_constraints)
            self._outgoing_subedges[subedge.pre_subvertex][partition_id]\
                .add_edge(subedge)

            self._subedge_to_partition[subedge] = \
                self._outgoing_subedges[subedge.pre_subvertex][partition_id]
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
        :param partition_id: the id for the outgoing partition that this edge\
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
            self, subvertex, partition_identifier=None):
        """ Locate the subedges for which subvertex is the pre_subvertex.\
            Can return an empty collection

        :param subvertex: the subvertex for which to find the outgoing subedges
        :type subvertex:\
                    :py:class:`pacman.model.partitioned_graph.partitioned_vertex.PartitionedVertex`
        :param partition_identifier: the identifier for the partition that
        the edges being returned should associate with. If set to None, returns
        all edges from all partitions
        :type partition_identifier: string or None
        :return: an iterable of subedges which have subvertex as their\
                    pre_subvertex
        :rtype: iterable of\
                    :py:class:`pacman.model.partitioned_graph.abstract_partitioned_edge.AbstractPartitionedEdge`
        :raise None: does not raise any known exceptions
        """
        if partition_identifier is None:
            edges = list()
            for partition_identifier in self._outgoing_subedges[subvertex]:
                edges.extend(
                    self._outgoing_subedges[subvertex][partition_identifier]
                    .edges)
            return edges
        elif partition_identifier not in self._outgoing_subedges[subvertex]:
            return ()
        else:
            return self._outgoing_subedges[subvertex][
                partition_identifier].edges

    def outgoing_edges_partitions_from_vertex(self, sub_vertex):
        """ Locates all the outgoing edge partitions for a given vertex

        :param sub_vertex: the vertex for which the outgoing edge partitions \
                    are to be located for.
         :type sub_vertex: \
                    :py:class:`pacman.model.partitionable_graph.abstract_partitionable_vertex.AbstractPartitionableVertex`
        :return: iterable of\
                     :py:class:`pacman.utilities.outgoing_edge_partition.OutgoingEdgePartition`
                     or a empty list if none are available
        :raise None: does not raise any known exceptions
        """
        if sub_vertex in self._outgoing_subedges:
            return self._outgoing_subedges[sub_vertex]
        else:
            return ()

    def get_partition_of_subedge(self, sub_edge):
        """ Locates the partition associated with a given subedge

        :param sub_edge: the subedge to locate the partition of
        :return: the partition or None
        """
        if sub_edge in self._subedge_to_partition:
            return self._subedge_to_partition[sub_edge]
        else:
            return None

    @property
    def partitions(self):
        """
        property method for all the partitions in the graph
        :return: iterable of\
                     :py:class:`pacman.utilities.outgoing_edge_partition.OutgoingEdgePartition`
        """
        partitions = list()
        for sub_vertex in self._subvertices:
            partition = self.outgoing_edges_partitions_from_vertex(sub_vertex)
            for partition_identifier in partition:
                partitions.append(partition[partition_identifier])
        return partitions

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

    def get_subvertex_with_repr(self, label):
        """ Locates the subvertex which has the same label of the input

        :param label: the input label to search for.
        :return: the partitionedVertex or None if there's no vertex with this\
                    label
        """
        if label in self._id_to_object_mapping:
            return self._id_to_object_mapping[label]
        else:
            return None

    def get_subedge_with_label(self, label, destination_sub_vertex=None):
        """ locates the subedge which has the same label of the input

        :param label: the input label to search for.
        :param destination_sub_vertex: the subvertex to which this edge goes to
        :return: the partitionedEdge or None if there's no vertex with this \
                    label
        """
        for subvertex in self._subvertices:
            for edge_partition_id in self._outgoing_subedges[subvertex]:
                vertex_and_partition_id = \
                    "{}:{}".format(id(subvertex), edge_partition_id)
                if vertex_and_partition_id == label:
                    edge_partition = \
                        self._outgoing_subedges[subvertex][edge_partition_id]
                    edges = edge_partition.edges
                    if destination_sub_vertex is None:
                        return edges[0]
                    else:
                        for edge in edges:
                            if edge.post_subvertex == destination_sub_vertex:
                                return edge
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

        :return: The label or None if there is no label
        :rtype: str
        :raise None: Raises no known exceptions
        """
        return self._label
