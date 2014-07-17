from pacman.model.subgraph.subvertex import Subvertex
from pacman.model.subgraph.subedge import Subedge
from pacman.exceptions import PacmanInvalidParameterException


class Subgraph(object):
    """ Represents a partitioning of a graph
    """

    def __init__(self, label=None, subvertices=None, subedges=None):
        """

        :param graph: the graph of which this is a subgraph
        :type graph: :py:class:`pacman.model.graph.graph.Graph`
        :param label: an identifier for the subgraph
        :type label: str
        :param subvertices: an iterable of vertices in the graph
        :type subvertices: iterable of\
                    :py:class:`pacman.model.subgraph.subvertex.Subvertex`
        :param subedges: an iterable of subedges in the graph
        :type subedges: iterable of\
                    :py:class:`pacman.model.subgraph.subedge.Subedge`
        :raise pacman.exceptions.PacmanInvalidParameterException:
                    * If one of the subedges is not valid
                    * If one of the subvertices is not valid
        """
        self._label = label
        self._subvertices = list()
        self._subedges = list()

        self._vertex_of_subvertex = dict()
        self._edge_of_subedge = dict()

        self._subvertices_of_vertex = dict()
        self._subedges_of_edge = dict()

        self._outgoing_subedges = dict()
        self._incoming_subedges = dict()

        self.add_subvertices(subvertices)
        self.add_subedges(subedges)

    def add_subvertex(self, subvertex, vertex=None):
        """ Add a subvertex to this subgraph

        :param subvertex: a subvertex to be added to the graph
        :type subvertex: :py:class:`pacman.model.subgraph.subvertex.Subvertex`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If the\
                    subvertex is not valid
        """
        if subvertex is None or not isinstance(subvertex, Subvertex):
            raise PacmanInvalidParameterException(
                    "subvertex", subvertex,
                    "Must be an instance of" 
                    " pacman.model.subgraph.subvertex.SubVertex")
        if subvertex.lo_atom < 0:
            raise  PacmanInvalidParameterException("lo_atom ", subvertex.lo_atom, "Cannot be less than 0")
        if subvertex.lo_atom > subvertex.hi_atom:
            raise  PacmanInvalidParameterException("hi_atom ", subvertex.hi_atom, "Cannot be less than lo_atom")

        if vertex is not None and vertex not in self._subvertices_of_vertex.keys():
            self._subvertices_of_vertex[vertex] = set()
            if subvertex.hi_atom >= vertex.n_atoms:
                raise  PacmanInvalidParameterException("hi_atom ", subvertex.hi_atom, "Cannot be greater than"
                                                                             " the total number of atoms")
        if subvertex in  self._subvertices_of_vertex[vertex]:
            raise PacmanInvalidParameterException("Subvertex", subvertex, "Cannot have duplicate subvertices in the subgraph")

        self._subvertices_of_vertex[vertex].add(subvertex)
        self._vertex_of_subvertex[subvertex] = vertex
        self._subvertices.append(subvertex)

        self._outgoing_subedges[subvertex] = list()
        self._incoming_subedges[subvertex] = list()

    def add_subvertices(self, subvertices, vertex = None):
        """ Add some subvertices to this subgraph

        :param subvertices: an iterable of subvertices to add to this subgraph
        :type subvertices: iterable of\
                    :py:class:`pacman.model.subgraph.subvertex.Subvertex`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If the\
                    subvertex is not valid
        """
        if subvertices is not None:
            for next_subvertex in subvertices:
                self.add_subvertex(next_subvertex, vertex)

    def add_subedge(self, subedge, edge = None):
        """ Add a subedge to this subgraph

        :param subedge: a subedge to be added to the subgraph
        :type subedge: :py:class:`pacman.model.subgraph.subedge.Subedge`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If the\
                    subedge is not valid
        """
        if subedge is None or not isinstance(subedge, Subedge):
            raise PacmanInvalidParameterException(
                    "subedge", subedge,
                    "Must be an instance of"
                    " pacman.model.subgraph.subedge.Subedge")

        # if self.pre_vertex not in pre_subvertex.:
        #     raise PacmanInvalidParameterException("pre_subvertex",pre_subvertex,"Must be a subvertex of this vertex")
        # if post_subvertex.vertex is not self.post_vertex:
        #     raise PacmanInvalidParameterException("post_subvertex",post_subvertex,"Must be a subvertex of this vertex")
        if edge is not None and edge not in self._subedges_of_edge.keys():
            self._subedges_of_edge[edge] = set()

        if subedge in  self._subedges_of_edge[edge]:
            raise PacmanInvalidParameterException("Subedge", subedge, "Cannot have duplicate subedges in the subgraph")

        self._subedges_of_edge[edge].add(subedge)
        self._edge_of_subedge[subedge] = edge
        self._subedges.append(subedge)
        
        self._outgoing_subedges[subedge.pre_subvertex].append(subedge)
        self._incoming_subedges[subedge.post_subvertex].append(subedge)

    def add_subedges(self, subedges, edge = None):
        """ Add some subedges to this subgraph

        :param subedges: an iterable of subedges to add to this subgraph
        :type subedges: iterable of\
                    :py:class:`pacman.model.subgraph.subedge.Subedge`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If the\
                    subedge is not valid
        """
        if subedges is not None:
            for next_subedge in subedges:
                self.add_subedge(next_subedge, edge)
                
    def remove_subedge(self, subedge):
        """ Remove a sub-edge from the subgraph
        
        :param subedge: The subedge to be removed
        :type subedge: :py:class:`pacman.model.subgraph.subedge.Subedge`
        :return: Nothing is returned
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If the\
                    subedge is not in the subgraph
        """
        subedge_position_in_list = -1
        for current_subedge_index in range(len(self.subedges)):
            if subedge is self.subedges[current_subedge_index]:
                subedge_position_in_list = current_subedge_index
                break

        if subedge.post_subvertex not in self._incoming_subedges.keys() \
                    or subedge.pre_subvertex not in self._outgoing_subedges.keys() or not subedge in self.subedges:
            raise PacmanInvalidParameterException("Subedge", subedge.label ," does not exist in the current subgraph")

        #Delete subedge entry in list of subedges
        del self.subedges[subedge_position_in_list]

        #Delete subedge from list in dictionary of outgoing subedges
        for current_subedge_index in range(len(self._outgoing_subedges[subedge])):
            if subedge is self._outgoing_subedges[subedge][current_subedge_index]:
                del self._outgoing_subedges[subedge][current_subedge_index]
                break
        #Delete subedge from list in dictionary of incoming subedges
        for current_subedge_index in range(len(self._incoming_subedges[subedge])):
            if subedge is self._incoming_subedges[subedge][current_subedge_index]:
                del self._incoming_subedges[subedge][current_subedge_index]
                break

        #Delete subedge from dictionary mapping from subedge to corresponding edge
        del self._edge_of_subedge[subedge]



    def outgoing_subedges_from_subvertex(self, subvertex):
        """ Locate the subedges for which subvertex is the pre_subvertex.\
            Can return an empty collection

        :param subvertex: the subvertex for which to find the outgoing subedges
        :type subvertex: :py:class:`pacman.model.subgraph.subvertex.Subvertex`
        :return: an iterable of subedges which have subvertex as their\
                    pre_subvertex
        :rtype: iterable of :py:class:`pacman.model.subgraph.subedge.Subedge`
        :raise None: does not raise any known exceptions
        """
        return self._outgoing_subedges[subvertex]

    def incoming_subedges_from_subvertex(self, subvertex):
        """ Locate the subedges for which subvertex is the post_subvertex.\
            Can return an empty collection.

        :param subvertex: the subvertex for which to find the incoming subedges
        :type subvertex: :py:class:`pacman.model.subgraph.subvertex.Subvertex`
        :return: an iterable of subedges which have subvertex as their\
                    post_subvertex
        :rtype: iterable of :py:class:`pacman.model.subgraph.subedge.Subedge`
        :raise None: does not raise any known exceptions
        """
        return self._incoming_subedges[subvertex]

    @property
    def subvertices(self):
        """ The subvertices of the subgraph

        :return: an iterable of subvertices
        :rtype: iterable of\
                    :py:class:`pacman.model.subgraph.subvertex.Subvertex`
        """
        return self._subvertices

    @property
    def subedges(self):
        """ The subedges of the subgraph

        :return: an iterable of subedges
        :rtype: iterable of\
                    :py:class:`pacman.model.subgraph.subedge.Subedge`
        """
        return self._subedges

    @property
    def label(self):
        """ The label of the subgraph

        :return: The label or None if there is no lable
        :rtype: str
        :raise None: Raises no known exceptions
        """
        return self._label


    def get_subvertices_from_vertex(self, vertex):
        """ supporting method to get all subvertices for a given vertex

        :param vertex: the vertex for which to find the associated subvertices
        :type vertex: pacman.model.graph.vertex.Vertex
        :return: a set of subvertices
        :rtype: iterable set
        :raise None: Raises no known exceptions
        """
        if vertex in self._subvertices_of_vertex.keys():
            return self._subvertices_of_vertex[vertex]
        return None
    
    def get_subedges_from_edge(self, edge):
        """ supporting method to get all subedges for a given edge

        :param edge: the edge for which to find the associated subedges
        :type edge: `pacman.model.graph.edge.Edge`
        :return: a set of subedges
        :rtype: iterable set
        :raise None: Raises no known exceptions
        """
        if edge in self._subedges_of_edge.keys():
            return self._subedges_of_edge[edge]
        return None

    def get_vertex_from_subvertex(self, subvertex):
        """ supporting method to get the vertex for a given subvertex

        :param subvertex: the edge for which to find the associated subedges
        :type subvertex: `pacman.model.subgraph.subvertex.Subvertex`
        :return: a vertex
        :rtype: `pacman.model.graph.vertex.Vertex`
        :raise None: Raises no known exceptions
        """
        if subvertex in self._vertex_of_subvertex.keys():
            return self._vertex_of_subvertex[subvertex]
        return None

    def get_edge_from_subedge(self, subedge):
        """ supporting method to get the edge for a given subedge

        :param subedge: the subedge for which to find the associated edge
        :type subedge: `pacman.model.subgraph.subedge.Subedge`
        :return: an edge
        :rtype: `pacman.model.graph.edge.Edge`
        :raise None: Raises no known exceptions
        """
        if subedge in self._edge_of_subedge.keys():
            return self._edge_of_subedge[subedge]
        return None