from pacman.model.partitioned_graph.abstract_partitioned_edge \
    import AbstractPartitionedEdge
from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex
from pacman.exceptions import (PacmanValueError,
                               PacmanNotFoundError,
                               PacmanTypeError)


class GraphMapper(object):
    """
    a mapping object between graphs.
    """

    def __init__(self, first_graph_label="", second_graph_label=""):
        self._vertex_from_subvertex = dict()
        self._edge_from_subedge = dict()

        self._subvertices_from_vertex = dict()
        self._subvertex_index = dict()
        self._subvertex_to_slice = dict()
        self._subvertex_slices = dict()
        self._subedges_from_edge = dict()
        self._first_graph_label = first_graph_label
        self._second_graph_label = second_graph_label

    @property
    def first_graph_label(self):
        """
        returns the label of the graph mapper's first graph.
        :return:
        """
        return self._first_graph_label

    def add_subvertex(self, subvertex, vertex_slice, vertex):
        """ Add a subvertex to this partitioned_graph

        :param subvertex: a subvertex to be added to the partitionable_graph
        :type subvertex:
                    :py:class:`pacman.model.partitioned_graph.partitioned_vertex.PartitionedVertex`
        :param vertex_slice: the chunk of atoms from the partitionable vertex
        that the partitioned vertex is going to represent
        :type vertex_slice:
        :py:class:`pacman.model.graph_mapper.slice.Slice`
        :param vertex: the partitionable vertex to associate this partitioned
        vertex with
        :type vertex: instance of
        :py:class:`pacman.model.partitionable_graph.abstract_partitionable_graph.AbstractPartitionableGraph`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanValueError: Atom selection is out of\
                    bounds.
        :raise pacman.exceptions.PacmanTypeError: If the subvertex is of an\
                    inappropriate type.
        """
        if not isinstance(subvertex, PartitionedVertex):
            raise PacmanTypeError(
                "subvertex", str(subvertex),
                "Must be an instance of"
                " pacman.model.partitioned_graph.subvertex.SubVertex")

        if vertex not in self._subvertices_from_vertex:
            self._subvertices_from_vertex[vertex] = list()
        if vertex not in self._subvertex_slices:
            self._subvertex_slices[vertex] = list()

        if vertex_slice.hi_atom >= vertex.n_atoms:
            raise PacmanValueError(
                "hi_atom {:d} >= maximum {:d}".format(vertex_slice.hi_atom,
                                                      vertex.n_atoms))

        self._vertex_from_subvertex[subvertex] = vertex
        subvertices = self._subvertices_from_vertex[vertex]
        self._subvertex_index[subvertex] = len(subvertices)
        subvertices.append(subvertex)
        self._subvertex_to_slice[subvertex] = vertex_slice
        self._subvertex_slices[vertex].append(vertex_slice)

    def add_partitioned_edge(self, partitioned_edge, partitionable_edge):
        """ Add a partitioned_edge to this partitioned_graph

        :param partitioned_edge: a partitioned_edge
        :type partitioned_edge:\
                   :py:class:`pacman.model.partitioned_graph.abstract_partitioned_edge.AbstractPartitionedEdge`
        :param partitionable_edge: the partitionable edge associated with the\
                    partitioned edge
        :type partitionable_edge:\
                    :py:class:`pacman.model.partitionable_graph.abstract_partitionable_edge.AbstractPartitionableEdge`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanTypeError: If the partitioned_edge is
            of an inappropriate type.
        """
        if (partitioned_edge is None or
                not isinstance(partitioned_edge, AbstractPartitionedEdge)):
            raise PacmanTypeError(
                "partitioned_edge", str(partitioned_edge),
                "Must be an AbstractPartitionedEdge")

        if (partitionable_edge is not None and partitionable_edge
                not in self._subedges_from_edge):
            self._subedges_from_edge[partitionable_edge] = set()

        if partitionable_edge is not None:
            self._subedges_from_edge[partitionable_edge].add(partitioned_edge)
            self._edge_from_subedge[partitioned_edge] = partitionable_edge

    def add_partitioned_edges(self, partitioned_edges, partitionable_edge):
        """ Add some partitioned_edges to this partitioned_graph

        :param partitioned_edges: an iterable of partitioned edges
        :type partitioned_edges: iterable of\
                    :py:class:`pacman.model.partitioned_graph.abstract_partitioned_edge.AbstractPartitionedEdge`
        :param partitionable_edge: Partitionable edge associated with the\
                    partitioned edges
        :type partitionable_edge:\
                    :py:class:`pacman.model.partitionable_graph.abstract_partitionable_edge.AbstractPartitionableEdge`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If the\
                    subedge is not valid
        """
        if partitioned_edges is not None:
            for next_subedge in partitioned_edges:
                self.add_partitioned_edge(next_subedge, partitionable_edge)

    def get_subvertices_from_vertex(self, vertex):
        """ Get all partitioned vertices for a given partitionable vertex

        :param vertex: the partitionable vertex for which to find the\
                    associated partitioned vertices
        :type vertex:\
                    :py:class:`pacman.model.partitionable_graph.abstract_partitionable_vertex.AbstractPartitionableVertex`
        :return: An iterable of partitioned vertices, or None if the vertex \
                    does not exist
        :rtype: iterable of\
                    :py:class:`pacman.model.partitioned_graph.partitioned_vertex.PartitionedVertex`\
                    or None
        :raise None: Raises no known exceptions
        """
        if vertex in self._subvertices_from_vertex:
            return self._subvertices_from_vertex[vertex]
        return None

    def get_subvertex_index(self, subvertex):
        """ Get the index of a subvertex within its list of vertices
        """
        return self._subvertex_index[subvertex]

    def get_partitioned_edges_from_partitionable_edge(self, edge):
        """ Get all partitioned edges associated with a partitionable edge

        :param edge: The partitionable edge to get the partitioned edges for
        :type edge:\
                    :py:class:`pacman.model.partitionable_graph.abstract_partitionable_edge.AbstractPartitionableEdge`
        :return: An iterable of partitioned edges or None if the edge does not\
                   exist
        :rtype: iterable of\
                    :py:class:`pacman.model.partitioned_graph.abstract_partitioned_edge.AbstractPartitionedEdge`\
                    or None
        """
        if edge in self._subedges_from_edge:
            return self._subedges_from_edge[edge]
        return None

    def get_vertex_from_subvertex(self, subvertex):
        """ Get a partitionable vertex for a given partitioned vertex

        :param subvertex: The partitioned vertex to get the partitionable\
                    of
        :type subvertex:\
                    :py:class:`pacman.model.partitioned_graph.partitioned_vertex.PartitionedVertex`
        :return: a partitionable vertex or None if the partitionable vertex\
                    does not exist
        :rtype:\
                    :py:class:`pacman.model.partitionable_graph.abstract_partitionable_vertex.AbstractPartitionableVertex`
        """
        if subvertex in self._vertex_from_subvertex:
            return self._vertex_from_subvertex[subvertex]
        return None

    def get_partitionable_edge_from_partitioned_edge(self, subedge):
        """ Get a partitionable edge from a partitioned edge

        :param subedge: The partitioned edge to get the partitionable edge of
        :type subedge:\
                    :py:class:`pacman.model.partitioned_graph.abstract_partitioned_edge.AbstractPartitionedEdge`
        :return: a partitionable edge or None if the partitioned edge does not\
                    exist
        :rtype:\
                    :py:class:`pacman.model.partitionable_graph.abstract_partitionable_edge.AbstractPartitionableEdge`
        :raise pacman.exceptions.PacmanNotFoundError: If the subedge is not
            known.
        """
        if subedge in self._edge_from_subedge:
            return self._edge_from_subedge[subedge]
        raise PacmanNotFoundError('{} not in graph mapper'.format(subedge))

    def get_subvertex_slice(self, subvertex):
        """ Get the slice of a partitioned vertex

        :param subvertex: the partitioned vertex to get the slice of
        :type subvertex:\
                    :py:class:`pacman.model.partitioned_graph.partitioned_vertex.PartitionedVertex`
        :return: a slice object containing the lo and hi atom or None if the\
                   partitioned vertex does not exist
        :rtype: :py:class:`pacman.model.graph_mapper.slice.Slice` or None
        """
        if subvertex in self._subvertex_to_slice:
            return self._subvertex_to_slice[subvertex]
        return None

    def get_subvertex_slices(self, vertex):
        """ Get all the slices of the subvertex
        """
        return self._subvertex_slices[vertex]

    def __repr__(self):
        return "graph_mapper object for between graphs \"{}\" and \"{}\""\
            .format(self._first_graph_label, self._second_graph_label)
