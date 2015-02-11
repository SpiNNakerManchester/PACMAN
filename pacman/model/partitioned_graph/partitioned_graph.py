from pacman.exceptions import PacmanInvalidParameterException
from pacman.exceptions import PacmanAlreadyExistsException

from pacman.utilities.ordered_set import OrderedSet


class PartitionedGraph(object):
    """ Represents a partitioning of a partitionable_graph
    """
    def __init__(self, label=None, subvertices=None, subedges=None):
        """

        :param label: an identifier for the partitioned_graph
        :type label: str
        :param subvertices: an iterable of vertices in the partitionable_graph
        :type subvertices: iterable of\
                    :py:class:`pacman.model.partitioned_graph.subvertex.PartitionedVertex`
        :param subedges: an iterable of subedges in the partitionable_graph
        :type subedges: iterable of\
                    :py:class:`pacman.model.partitioned_graph.subedge.PartitionedEdge`
        :raise pacman.exceptions.PacmanInvalidParameterException:
                    * If one of the subedges is not valid
                    * If one of the subvertices is not valid
        """
        self._label = label
        self._subvertices = OrderedSet()
        self._subedges = OrderedSet()

        self._outgoing_subedges = dict()
        self._incoming_subedges = dict()

        self.add_subvertices(subvertices)
        self.add_subedges(subedges)

    def add_subvertex(self, subvertex):
        """ Add a subvertex to this partitioned_graph

        :param subvertex: a subvertex to be added to the partitionable_graph
        :type subvertex: :py:class:`pacman.model.subgraph.subvertex.PartitionedVertex`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If the\
                    subvertex is not valid
        """
        if subvertex not in self._subvertices:
            self._subvertices.add(subvertex)
        else:
            raise PacmanAlreadyExistsException("PartitionedVertex", str(subvertex))
        self._outgoing_subedges[subvertex] = list()
        self._incoming_subedges[subvertex] = list()

    def add_subvertices(self, subvertices):
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
                self.add_subvertex(next_subvertex)

    def add_subedge(self, subedge):
        """ Add a subedge to this partitioned_graph

        :param subedge: a subedge to be added to the partitioned_graph
        :type subedge: :py:class:`pacman.model.subgraph.subedge.PartitionedEdge`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If the\
                    subedge is not valid
        """
        if subedge in self._subedges:
            raise PacmanAlreadyExistsException("PartitionedEdge", str(subedge))

        self._subedges.add(subedge)

        if subedge.pre_subvertex in self._outgoing_subedges.keys():
            self._outgoing_subedges[subedge.pre_subvertex].append(subedge)
        else:
            raise PacmanInvalidParameterException(
                "PartitionedEdge pre_subvertex", str(subedge.pre_subvertex),
                " Must exist in the partitioned_graph")

        if subedge.post_subvertex in self._incoming_subedges.keys():
            self._incoming_subedges[subedge.post_subvertex].append(subedge)
        else:
            raise PacmanInvalidParameterException(
                "PartitionedEdge post_subvertex", str(subedge.post_subvertex),
                " Must exist in the partitioned_graph")

    def add_subedges(self, subedges):
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
                self.add_subedge(next_subedge)

    def outgoing_subedges_from_subvertex(self, subvertex):
        """ Locate the subedges for which subvertex is the pre_subvertex.\
            Can return an empty collection

        :param subvertex: the subvertex for which to find the outgoing subedges
        :type subvertex: :py:class:`pacman.model.subgraph.subvertex.PartitionedVertex`
        :return: an iterable of subedges which have subvertex as their\
                    pre_subvertex
        :rtype: iterable of :py:class:`pacman.model.partitioned_graph.subedge.PartitionedEdge`
        :raise None: does not raise any known exceptions
        """
        if subvertex in self._outgoing_subedges.keys():
            return self._outgoing_subedges[subvertex]
        return None

    def incoming_subedges_from_subvertex(self, subvertex):
        """ Locate the subedges for which subvertex is the post_subvertex.\
            Can return an empty collection.

        :param subvertex: the subvertex for which to find the incoming subedges
        :type subvertex: :py:class:`pacman.model.subgraph.subvertex.PartitionedVertex`
        :return: an iterable of subedges which have subvertex as their\
                    post_subvertex
        :rtype: iterable of :py:class:`pacman.model.partitioned_graph.subedge.PartitionedEdge`
        :raise None: does not raise any known exceptions
        """
        if subvertex in self._incoming_subedges.keys():
            return self._incoming_subedges[subvertex]
        return None

    @property
    def subvertices(self):
        """ The subvertices of the partitioned_graph

        :return: an iterable of subvertices
        :rtype: iterable of\
                    :py:class:`pacman.model.partitioned_graph.subvertex.PartitionedVertex`
        """
        return self._subvertices

    @property
    def subedges(self):
        """ The subedges of the partitioned_graph

        :return: an iterable of subedges
        :rtype: iterable of\
                    :py:class:`pacman.model.partitioned_graph.subedge.PartitionedEdge`
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