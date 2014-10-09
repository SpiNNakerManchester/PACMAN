from pacman.model.partitioned_graph.partitioned_edge import PartitionedEdge
from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex
from pacman.exceptions import PacmanInvalidParameterException
from pacman.model.graph_mapper.slice import Slice


class GraphMapper(object):

    def __init__(self, first_graph_label="", second_graph_label=""):
        """
        :return:
        """
        self._vertex_from_subvertex = dict()
        self._edge_from_subedge = dict()

        self._subvertices_from_vertex = dict()
        self._subvertex_to_slice = dict()
        self._subedges_from_edge = dict()
        self._first_graph_label = first_graph_label
        self._second_graph_label = second_graph_label

    @property
    def first_graph_label(self):
        return self._first_graph_label

    def add_subvertex(self, subvertex, lo_atom, hi_atom, vertex):
        """ Add a subvertex to this partitioned_graph

        :param subvertex: a subvertex to be added to the partitionable_graph
        :type subvertex: :py:class:`pacman.model.subgraph.subvertex.PartitionedVertex`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If the\
                    subvertex is not valid
        """
        if subvertex is None or not isinstance(subvertex, PartitionedVertex):
            raise PacmanInvalidParameterException(
                "subvertex", str(subvertex),
                "Must be an instance of"
                " pacman.model.partitioned_graph.subvertex.SubVertex")
        if lo_atom < 0:
            raise PacmanInvalidParameterException("lo_atom ",
                                                  str(lo_atom),
                                                  "Cannot be less than 0")
        if lo_atom > hi_atom:
            raise PacmanInvalidParameterException(
                "hi_atom ",
                str(subvertex.hi_atom),
                "Cannot be less than lo_atom")

        if vertex not in self._subvertices_from_vertex:
            self._subvertices_from_vertex[vertex] = set()

        if hi_atom >= vertex.n_atoms:
            raise PacmanInvalidParameterException(
                "hi_atom ", str(hi_atom),
                "Cannot be greater than the total number of atoms")

        self._vertex_from_subvertex[subvertex] = vertex
        self._subvertices_from_vertex[vertex].add(subvertex)
        self._subvertex_to_slice[subvertex] = Slice(lo_atom=lo_atom,
                                                    hi_atom=hi_atom)

    def add_partitioned_edge(self, partitioned_edge, partitionable_edge):
        """ Add a partitioned_edge to this partitioned_graph

        :param partitioned_edge: a partitioned_edge to be added to the partitioned_graph
        :type partitioned_edge: :py:class:`pacman.model.partitioned_graph.partitionedEdge.PartitionedEdge`
        :param partitionable_edge: the partitionable_edge associated with this partitioned_edge
        :type partitionable_edge:
        :py:class:`pacman.model.partitionable_graph.partitionable_edge.PartitionableEdge`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If the\
                    partitioned_edge is not valid
        """
        if (partitioned_edge is None or
                not isinstance(partitioned_edge, PartitionedEdge)):
            raise PacmanInvalidParameterException(
                "partitioned_edge", str(partitioned_edge),
                "Must be an instance of"
                " pacman.model.partitioned_graph.partitionedEdge"
                ".PartitionedEdge")

        if (partitionable_edge is not None and partitionable_edge
                not in self._subedges_from_edge.keys()):
            self._subedges_from_edge[partitionable_edge] = set()

        if partitionable_edge is not None:
            self._subedges_from_edge[partitionable_edge].add(partitioned_edge)
            self._edge_from_subedge[partitioned_edge] = partitionable_edge

    def add_partitioned_edges(self, partitioned_edges, partitionable_edge):
        """ Add some partitioned_edges to this partitioned_graph

        :param partitioned_edges: an iterable of partitioned_edges to add to this partitioned_graph
        :param partitioned_edges : partitioned_edges iterable of\
                    :py:class:`pacman.model.partitioned_graph.subedge.PartitionedEdge`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If the\
                    subedge is not valid
        """
        if partitioned_edges is not None:
            for next_subedge in partitioned_edges:
                self.add_partitioned_edge(next_subedge, partitionable_edge)

    def get_subvertices_from_vertex(self, vertex):
        """ supporting method to get all subvertices for a given vertex

        :param vertex: the vertex for which to find the associated subvertices
        :type vertex: pacman.model.graph.vertex.AbstractConstrainedVertex
        :return: a set of subvertices or None if no vertex exists in the mappings
        :rtype: iterable set or None
        :raise None: Raises no known exceptions
        """
        if vertex in self._subvertices_from_vertex.keys():
            return self._subvertices_from_vertex[vertex]
        return None

    def get_partitioned_edges_from_partitionable_edge(self, edge):
        """ supporting method to get all subedges for a given edge

        :param edge: the edge for which to find the associated subedges
        :type edge: `pacman.model.graph.edge.PartitionableEdge`
        :return: a set of subedges
        :rtype: iterable set or none
        :raise None: Raises no known exceptions
        """
        if edge in self._subedges_from_edge.keys():
            return self._subedges_from_edge[edge]
        return None

    def get_vertex_from_subvertex(self, subvertex):
        """ supporting method to get the vertex for a given subvertex

        :param subvertex: the edge for which to find the associated subedges
        :type subvertex: `pacman.model.subgraph.subvertex.PartitionedVertex`
        :return: a vertex
        :rtype: `pacman.model.graph.vertex.AbstractConstrainedVertex`
        :raise None: Raises no known exceptions
        """
        if subvertex in self._vertex_from_subvertex.keys():
            return self._vertex_from_subvertex[subvertex]
        return None

    def get_partitionable_edge_from_partitioned_edge(self, subedge):
        """ supporting method to get the edge for a given subedge

        :param subedge: the subedge for which to find the associated edge
        :type subedge: `pacman.model.subgraph.subedge.PartitionedEdge`
        :return: an edge
        :rtype: `pacman.model.graph.edge.PartitionableEdge`
        :raise None: Raises no known exceptions
        """
        if subedge in self._edge_from_subedge.keys():
            return self._edge_from_subedge[subedge]
        return None

    def get_subvertex_slice(self, subvertex):
        """ supporting method for retrieveing the lo and hi atom of a subvertex

        :param subvertex: the subvertex to locate the slice of
        :return: a slice object containing the lo and hi atom of a subvertex
        :rtype: pacman.model.graph_mapper.slice.Slice
        :raise PacmanInvalidParameterException: when the subvertex is none or
        the subvertex is not contianed within the mapping object
        """
        if subvertex is None or subvertex not in self._subvertex_to_slice.keys():
            raise PacmanInvalidParameterException(
                "subvertex", str(subvertex),
                "Must be an instance of"
                " pacman.model.partitioned_graph.partitioned_vertex."
                "PartitionedVertex")
        else:
            return self._subvertex_to_slice[subvertex]

    def __repr__(self):
        return "graph_mapper object for between graphs \"{}\" and \"{}\""\
            .format(self._first_graph_label, self._second_graph_label)