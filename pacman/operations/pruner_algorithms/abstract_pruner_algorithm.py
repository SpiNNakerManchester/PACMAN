from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass

@add_metaclass(ABCMeta)
class AbstractPrunerAlgorithm(object):
    """ An abstract algorithm that can prune a subgraph
    """
    
    @abstractmethod
    def prune(self, subgraph):
        """ Prune items from a subgraph that are not required
            
        :param subgraph: The subgraph to prune
        :type subgraph: :py:class:`pacman.model.subgraph.subgraph.Subgraph`
        :return: The items which are prunable
        :rtype: :py:class:`pacman.model.prunables.prunables.Prunables`
        :raise pacman.exceptions.PacmanPruneException: If something\
                   goes wrong with the pruning
        """
        pass
