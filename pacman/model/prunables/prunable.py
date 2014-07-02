class Prunable(object):
    """ Represents a subedge that can be pruned
    """

    def __init__(self, subedge):
        """

        :param subedge: a subedge which can be pruned
        :type subedge: :py:class:`pacman.model.subgraph.subedge.Subedge`
        :raise None: does not raise any known exceptions
        """
        pass

    @property
    def subedge(self):
        """ The subedge which can be pruned

        :return: the subedge which may be pruned
        :rtype: :py:class:`pacman.model.subgraph.subedge.Subedge`
        :raise None: does not raise any known exceptions
        """
        pass
