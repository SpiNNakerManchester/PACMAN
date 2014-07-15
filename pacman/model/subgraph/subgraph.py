from pacman.model.subgraph.subvertex import Subvertex
from pacman.model.subgraph.subedge import Subedge
from pacman.exceptions import PacmanInvalidParameterException


class Subgraph(object):
    """ Represents a partitioning of a graph
    """

    def __init__(self, graph, label=None, subvertices=None, subedges=None):
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
        self._graph = graph
        self._subvertices = list()
        self._subedges = list()

        self.add_subvertices(subvertices)
        self.add_subedges(subedges)

    def add_subvertex(self, subvertex):
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
        self._subvertices.append(subvertex)

    def add_subvertices(self, subvertices):
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
                self.add_subvertex(next_subvertex)

    def add_subedge(self, subedge):
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
        self._subedges.append(subedge)

    def add_subedges(self, subedges):
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
                self.add_subedge(next_subedge)
                
    def remove_subedge(self, subedge):
        """ Remove a sub-edge from the subgraph
        
        :param subedge: The subedge to be removed
        :type subedge: :py:class:`pacman.model.subgraph.subedge.Subedge`
        :return: Nothing is returned
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If the\
                    subedge is not in the subgraph
        """
        pass

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
        outgoing_subedges = list()

        for subedge in self._subedges:
            if subedge.pre_subvertex == subvertex:
                outgoing_subedges.append(subedge)

        return outgoing_subedges

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
        return_list = list()

        for temp_subedge in self._subedges:
            if temp_subedge.post_subvertex == subvertex:
                return_list.append(temp_subedge)

        return return_list

    @property
    def graph(self):
        """ The graph of which this is a subgraph
        
        :return: a graph object
        :rtype: :py:class:`pacman.model.graph.graph.Graph`
        """
        return self._graph

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
        """ supporting method to get all subverts for a given vertex

        :param vertex: the vertex for which to find the associated subvertexes
        :type vertex: pacman.model.graph.vertex.Vertex
        :return: a list of subvertices
        :rtype: iterable list
        :raise None: Raises no known exceptions
        """
        pass