import collections

from pacman.model.graph_mapper.slice import Slice


PartitionedVertexAttributes = collections.namedtuple(
    'PartitionedVertexAttributes', 'vertex slice')
PartitionedEdgeAttributes = collections.namedtuple(
    'PartitionedEdgeAttributes', 'edge')


class GraphMapper(object):

    def __init__(self, first_graph_label="", second_graph_label=""):
        """
        :return:
        """
        self.partitioned_vertices = dict()
        self.partitioned_edges = dict()

        self._first_graph_label = first_graph_label
        self._second_graph_label = second_graph_label

    @property
    def first_graph_label(self):
        return self._first_graph_label

    def add_subvertex(self, subvertex, lo_atom, hi_atom, vertex=None):
        """ Add a subvertex to this partitioned_graph

        :param subvertex: a subvertex to be added to the partitionable_graph
        :type subvertex:
            :py:class:`pacman.model.subgraph.subvertex.PartitionedVertex`
        :return: None
        :rtype: None
        :raise ValueError: If the `lo_atom`, `hi_atom` values are invalid.
        """
        if lo_atom < 0:
            raise ValueError("lo_atom {:d} is negative.".format(lo_atom))

        if lo_atom > hi_atom:
            raise ValueError("hi_atom {:d} < lo_atom {:d}".format(hi_atom,
                                                                  lo_atom))

        if vertex is not None:
            if hi_atom >= vertex.n_atoms:
                raise ValueError(
                    "hi_atom {:d} > max {:d}".format(hi_atom, vertex.n_atoms))

        self.partitioned_vertices[subvertex] = PartitionedVertexAttributes(
            vertex, Slice(lo_atom=lo_atom, hi_atom=hi_atom))

    def add_partitioned_edge(self, partitioned_edge, partitionable_edge=None):
        """ Add a partitioned_edge to this partitioned_graph

        :param partitioned_edge: a partitioned_edge to be added to the
            partitioned_graph
        :type partitioned_edge:
            :py:class:`pacman.model.partitioned_graph.partitioned_edge.PartitionedEdge`
        :param partitionable_edge: the partitionable_edge associated with this
            partitioned_edge
        :type partitionable_edge:
        :py:class:`pacman.model.partitionable_graph.partitionable_edge.PartitionableEdge`
        :return: None
        :rtype: None
        :raise None: No known exceptions.
        """
        self.partitioned_edges[partitioned_edge] = PartitionedEdgeAttributes(
            partitionable_edge)

    def add_partitioned_edges(self, partitioned_edges, partitionable_edge):
        """ Add some partitioned_edges to this partitioned_graph

        :param partitioned_edges: an iterable of partitioned_edges to add to
            this partitioned_graph
        :param partitioned_edges : partitioned_edges iterable of\
            :py:class:`pacman.model.partitioned_graph.subedge.PartitionedEdge`
        :return: None
        :rtype: None
        :raise None: No known errors.
        """
        for subedge in partitioned_edges:
            self.add_partitioned_edge(subedge, partitionable_edge)

    def get_subvertices_from_vertex(self, vertex):
        """ supporting method to get all subvertices for a given vertex

        :param vertex: the vertex for which to find the associated subvertices
        :type vertex: pacman.model.graph.vertex.AbstractConstrainedVertex
        :return: Set of subvertices.
        :rtype: set
        :raise KeyError: If the vertex is not known.
        """
        partitioned_vertices = list(self.get_matching_partitioned_vertices(
            lambda pv: self.get_vertex_from_subvertex(pv) is vertex)
        )
        if len(partitioned_vertices) == 0:
            raise KeyError(vertex)
        return partitioned_vertices

    def get_partitioned_edges_from_partitionable_edge(self, edge):
        """ supporting method to get all subedges for a given edge

        :param edge: the edge for which to find the associated subedges
        :type edge: `pacman.model.graph.edge.PartitionableEdge`
        :return: Set of subedges.
        :rtype: set
        :raise KeyError: If the edge is not known.
        """
        partitioned_edges = list(self.get_matching_partitioned_edges(
            lambda pe: (self.get_partitionable_edge_from_partitioned_edge(pe)
                        is edge)
        ))

        if len(partitioned_edges) == 0:
            raise KeyError(edge)
        return partitioned_edges

    def get_vertex_from_subvertex(self, subvertex):
        """ supporting method to get the vertex for a given subvertex

        :param subvertex: the edge for which to find the associated subedges
        :type subvertex: `pacman.model.subgraph.subvertex.PartitionedVertex`
        :return: a vertex
        :rtype: `pacman.model.graph.vertex.AbstractConstrainedVertex`
        :raise KeyError: If subvertex is not known.
        """
        if subvertex not in self.partitioned_vertices:
            raise KeyError(subvertex)
        return self.partitioned_vertices[subvertex].vertex

    def get_partitionable_edge_from_partitioned_edge(self, subedge):
        """ supporting method to get the edge for a given subedge

        :param subedge: the subedge for which to find the associated edge
        :type subedge: `pacman.model.subgraph.subedge.PartitionedEdge`
        :return: an edge
        :rtype: `pacman.model.graph.edge.PartitionableEdge`
        :raise KeyError: if subedge is not known.
        """
        if subedge not in self.partitioned_edges:
            raise KeyError(subedge)
        return self.partitioned_edges[subedge].edge

    def get_subvertex_slice(self, subvertex):
        """ supporting method for retrieveing the lo and hi atom of a subvertex

        :param subvertex: the subvertex to locate the slice of
        :return: a slice object containing the lo and hi atom of a subvertex
        :rtype: pacman.model.graph_mapper.slice.Slice
        :raise KeyError: If the subvertex is not known.
        """
        if subvertex not in self.partitioned_vertices:
            raise KeyError(subvertex)
        return self.partitioned_vertices[subvertex].slice

    def get_matching_partitioned_vertices(self, predicate):
        """A generator of partitioned vertices which match the predicate.

        The predicate is expected to receive a partitioned vertex as its only
        argument.
        """
        for pv in self.partitioned_vertices.iterkeys():
            if predicate(pv):
                yield pv

    def get_matching_partitioned_edges(self, predicate):
        """A generator of partitioned edges which match the predicate.

        The predicate is expected to receive a partitioned edge as its only
        argument.
        """
        for pe in self.partitioned_edges.iterkeys():
            if predicate(pe):
                yield pe

    def __repr__(self):
        return "graph_mapper object for between graphs \"{}\" and \"{}\""\
            .format(self._first_graph_label, self._second_graph_label)
