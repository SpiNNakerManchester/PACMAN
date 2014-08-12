from pacman.model.partitioned_graph.partitioned_edge import PartitionedEdge
from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex
from pacman.exceptions import PacmanInvalidParameterException


class GraphSubgraphMapper(object):

    def __init__(self):
        """
        :return:
        """
        self._vertex_from_subvertex = dict()
        self._edge_from_subedge = dict()

        self._subvertices_from_vertex = dict()
        self._subedges_from_edge = dict()

    def add_subvertex(self, subvertex, vertex=None):
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
        if subvertex.lo_atom < 0:
            raise PacmanInvalidParameterException("lo_atom ",
                                                  str(subvertex.lo_atom),
                                                  "Cannot be less than 0")
        if subvertex.lo_atom > subvertex.hi_atom:
            raise PacmanInvalidParameterException(
                "hi_atom ",
                str(subvertex.hi_atom),
                "Cannot be less than lo_atom")

        if vertex is not None \
                and vertex not in self._subvertices_from_vertex.keys():
            self._subvertices_from_vertex[vertex] = set()
            if subvertex.hi_atom >= vertex.n_atoms:
                raise PacmanInvalidParameterException(
                    "hi_atom ", str(subvertex.hi_atom),
                    "Cannot be greater than the total number of atoms")

        if vertex is not None:
            self._vertex_from_subvertex[subvertex] = vertex
            self._subvertices_from_vertex[vertex].add(subvertex)

    def add_subvertices(self, subvertices, vertex=None):
        """ Add some subvertices to this partitioned_graph

        :param subvertices: an iterable of subvertices to add to this partitioned_graph
        :type subvertices: iterable of\
                    :py:class:`pacman.model.partitioned_graph.subvertex.PartitionedVertex`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If the\
                    subvertex is not valid
        """
        if subvertices is not None:
            for next_subvertex in subvertices:
                self.add_subvertex(next_subvertex, vertex)

    def add_subedge(self, subedge, edge=None):
        """ Add a subedge to this partitioned_graph

        :param subedge: a subedge to be added to the partitioned_graph
        :type subedge: :py:class:`pacman.model.subgraph.subedge.PartitionedEdge`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If the\
                    subedge is not valid
        """
        if subedge is None or not isinstance(subedge, PartitionedEdge):
            raise PacmanInvalidParameterException(
                "subedge", str(subedge),
                "Must be an instance of"
                " pacman.model.partitioned_graph.subedge.PartitionedEdge")

        if edge is not None and edge not in self._subedges_from_edge.keys():
            self._subedges_from_edge[edge] = set()

        if edge is not None:
            self._subedges_from_edge[edge].add(subedge)
            self._edge_from_subedge[subedge] = edge

    def add_subedges(self, subedges, edge=None):
        """ Add some subedges to this partitioned_graph

        :param subedges: an iterable of subedges to add to this partitioned_graph
        :type subedges: iterable of\
                    :py:class:`pacman.model.partitioned_graph.subedge.PartitionedEdge`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If the\
                    subedge is not valid
        """
        if subedges is not None:
            for next_subedge in subedges:
                self.add_subedge(next_subedge, edge)

    def get_subvertices_from_vertex(self, vertex):
        """ supporting method to get all subvertices for a given vertex

        :param vertex: the vertex for which to find the associated subvertices
        :type vertex: pacman.model.graph.vertex.Vertex
        :return: a set of subvertices or None if no vertex exists in the mappings
        :rtype: iterable set or None
        :raise None: Raises no known exceptions
        """
        if vertex in self._subvertices_from_vertex.keys():
            return self._subvertices_from_vertex[vertex]
        return None

    def get_subedges_from_edge(self, edge):
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
        :rtype: `pacman.model.graph.vertex.Vertex`
        :raise None: Raises no known exceptions
        """
        if subvertex in self._vertex_from_subvertex.keys():
            return self._vertex_from_subvertex[subvertex]
        return None

    def get_edge_from_subedge(self, subedge):
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