"""
OutgoingEdgePartition
"""


class OutgoingEdgePartition(object):
    """
    A collection of egdes which have the same semantics
    """

    def __init__(self, identifier):
        self._identifier = identifier
        self._edges = list()

    def add_edge(self, edge):
        """
        adds a edge into this outgoing edge partition
        :param edge: the instance of abstract edge to add to the list
        :return:
        """
        self._edges.append(edge)

    @property
    def identifer(self):
        """
        returns the indenfiter for this outgoing egde partition
        :return:
        """
        return self._identifier

    @property
    def edges(self):
        """
        returns the edges that are associated with this outgoing egde partition
        :return:
        """
        return self._edges