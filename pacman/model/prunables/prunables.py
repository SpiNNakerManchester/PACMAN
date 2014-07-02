class Prunables(object):
    """ Maintains a list of items that can be pruned from the subgraph
    """

    def __init__(self, prunables=None):
        """
        :param prunables: iterable of prunables to add
        :type prunables: iterable of\
                    :py:class:`pacman.model.prunables.prunable.Prunable`
        :raise None: does not raise any known exceptions
        """
        pass

    def add_prunable(self, pruable):
        """ Add a prunable

        :param prunable: The prunable to add
        :type prunable: :py:class:`pacman.model.prunables.prunable.Prunable`
        :return: None
        :rtype: None
        :raise None: does not raise any known exceptions
        """
        pass
    
    def is_prunable(self, subedge):
        """ Determines if a subedge can be pruned
        
        :param subedge: The subedge to determine the prunable status of
        :type subedge: :py:class:`pacman.model.subgraph.subedge.Subedge`
        :return: True if the subedge is marked as prunable, False otherwise
        :rtype: bool
        """
        pass

    @property
    def prunables(self):
        """ The prunables

        :return: iterable of prunables
        :rtype: iterable of :py:class:`pacman.model.prunables.prunable.Prunable`
        :raise None: does not raise any known exceptions
        """
        pass
