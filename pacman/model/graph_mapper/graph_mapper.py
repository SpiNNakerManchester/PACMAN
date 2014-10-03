import collections

from pacman.model.graph_mapper.slice import Slice


class GraphMapper(object):

    def __init__(self, first_graph_label="", second_graph_label=""):
        """
        :return:
        """
        self._vertex_from_subvertex = dict()
        self._edge_from_subedge = dict()

        self._subvertices_from_vertex = collections.defaultdict(set)
        self._subvertex_to_slice = dict()
        self._subedges_from_edge = collections.defaultdict(set)
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

            self._vertex_from_subvertex[subvertex] = vertex
            self._subvertices_from_vertex[vertex].add(subvertex)

        self._subvertex_to_slice[subvertex] = Slice(lo_atom=lo_atom,
                                                    hi_atom=hi_atom)

    def add_subedge(self, subedge, edge=None):
        """ Add a subedge to this partitioned_graph

        :param subedge: a subedge to be added to the partitioned_graph
        :type subedge:
            :py:class:`pacman.model.subgraph.subedge.PartitionedEdge`
        :return: None
        :rtype: None
        :raise None: No known errors.
        """
        self._subedges_from_edge[edge].add(subedge)
        self._edge_from_subedge[subedge] = edge

    def add_subedges(self, subedges, edge=None):
        """ Add some subedges to this partitioned_graph

        :param subedges: an iterable of subedges to add to this
            partitioned graph
        :type subedges: iterable of\
            :py:class:`pacman.model.partitioned_graph.subedge.PartitionedEdge`
        :return: None
        :rtype: None
        :raise None: No known errors.
        """
        for subedge in subedges:
            self.add_subedge(subedge, edge)

    def get_subvertices_from_vertex(self, vertex):
        """ supporting method to get all subvertices for a given vertex

        :param vertex: the vertex for which to find the associated subvertices
        :type vertex: pacman.model.graph.vertex.AbstractConstrainedVertex
        :return: Set of subvertices.
        :rtype: set
        :raise KeyError: If the vertex is not known.
        """
        if vertex not in self._subvertices_from_vertex:
            raise KeyError(vertex)
        return self._subvertices_from_vertex[vertex]

    def get_subedges_from_edge(self, edge):
        """ supporting method to get all subedges for a given edge

        :param edge: the edge for which to find the associated subedges
        :type edge: `pacman.model.graph.edge.PartitionableEdge`
        :return: Set of subedges.
        :rtype: set
        :raise KeyError: If the edge is not known.
        """
        if edge not in self._subedges_from_edge:
            raise KeyError(edge)
        return self._subedges_from_edge[edge]

    def get_vertex_from_subvertex(self, subvertex):
        """ supporting method to get the vertex for a given subvertex

        :param subvertex: the edge for which to find the associated subedges
        :type subvertex: `pacman.model.subgraph.subvertex.PartitionedVertex`
        :return: a vertex
        :rtype: `pacman.model.graph.vertex.AbstractConstrainedVertex`
        :raise KeyError: If subvertex is not known.
        """
        if subvertex in self._vertex_from_subvertex:
            raise KeyError(subvertex)
        return self._vertex_from_subvertex[subvertex]

    def get_edge_from_subedge(self, subedge):
        """ supporting method to get the edge for a given subedge

        :param subedge: the subedge for which to find the associated edge
        :type subedge: `pacman.model.subgraph.subedge.PartitionedEdge`
        :return: an edge
        :rtype: `pacman.model.graph.edge.PartitionableEdge`
        :raise KeyError: if subedge is not known.
        """
        if subedge in self._edge_from_subedge:
            raise KeyError(subedge)
        return self._edge_from_subedge[subedge]

    def get_subvertex_slice(self, subvertex):
        """ supporting method for retrieveing the lo and hi atom of a subvertex

        :param subvertex: the subvertex to locate the slice of
        :return: a slice object containing the lo and hi atom of a subvertex
        :rtype: pacman.model.graph_mapper.slice.Slice
        :raise KeyError: If the subvertex is not known.
        """
        if subvertex not in self._subvertex_to_slice:
            raise KeyError(subvertex)
        return self._subvertex_to_slice[subvertex]

    def __repr__(self):
        return "graph_mapper object for between graphs \"{}\" and \"{}\""\
            .format(self._first_graph_label, self._second_graph_label)
