__author__ = 'daviess'


class Prunable(object):
    """
    Creates an object to declare that a subedge may be pruned
    """

    def __init__(self, subedge):
        """

        :param subedge: a subedge which may be pruned
        :type subedge: pacman.subgraph.subedge.Subedge
        :return: a prunable object containing the subedge which may be pruned
        :rtype: pacman.pruning_info.prunable.Prunable
        :raises None: does not raise any known exceptions
        """
        pass

    @property
    def subedge(self):
        """
        Returns the subedge which may be pruned

        :return: the subedge which may be pruned
        :rtype: pacman.subgraph.subedge.Subedge
        :raises None: does not raise any known exceptions
        """
        pass
