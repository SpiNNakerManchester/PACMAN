__author__ = 'daviess'


class PruningInfo(object):
    """
    A list of prunable objects identifying the subedges which may be pruned from the subgraph
    """

    def __init__(self):
        """

        :return: a new PruningInfo object
        :rtype: pacman.pruning_info.pruning_info.PruningInfo
        :raise None: does not raise any known exceptions
        """
        pass

    def add_prunable(self, subedge):
        """
        Add a subedge to the prunable edges collection

        :param subedge: a subedge which may be pruned
        :type subedge: pacman.subgraph.subedge.Subedge
        :return: None
        :rtype: None
        :raise None: does not raise any known exceptions
        """
        pass

    @property
    def prunables(self):
        """
        Returns the list of prunable subedges

        :return: the list of prunable edges
        :rtype: list of pacman.subgraph.subedge.Subedge
        :raise None: does not raise any known exceptions
        """
        pass
