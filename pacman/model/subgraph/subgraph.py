from pacman.exceptions import PacmanInvalidParameterException
from pacman.exceptions import PacmanAlreadyExistsException


class Subgraph(object):
    """ Represents a partitioning of a graph
    """
    def __init__(self, label=None, subvertices=None, subedges=None):
        """

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
        self._subvertices = set()
        self._subedges = set()

        self._outgoing_subedges = dict()
        self._incoming_subedges = dict()

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
        if subvertex not in self._subvertices:
            self._subvertices.add(subvertex)
        else:
            raise PacmanAlreadyExistsException("Subvertex", str(subvertex))
        self._outgoing_subedges[subvertex] = list()
        self._incoming_subedges[subvertex] = list()

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
        if subedge in self._subedges:
            raise PacmanAlreadyExistsException("Subedge", str(subedge))

        self._subedges.add(subedge)

        if subedge.pre_subvertex in self._outgoing_subedges.keys():
            self._outgoing_subedges[subedge.pre_subvertex].append(subedge)
        else:
            raise PacmanInvalidParameterException(
                "Subedge pre_subvertex", str(subedge.pre_subvertex),
                " Must exist in the subgraph")

        if subedge.post_subvertex in self._incoming_subedges.keys():
            self._incoming_subedges[subedge.post_subvertex].append(subedge)
        else:
            raise PacmanInvalidParameterException(
                "Subedge post_subvertex", str(subedge.post_subvertex),
                " Must exist in the subgraph")

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
        if subvertex in self._outgoing_subedges.keys():
            return self._outgoing_subedges[subvertex]
        return None

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
        if subvertex in self._incoming_subedges.keys():
            return self._incoming_subedges[subvertex]
        return None

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