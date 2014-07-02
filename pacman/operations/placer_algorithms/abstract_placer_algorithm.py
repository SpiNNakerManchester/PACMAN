from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass

@add_metaclass(ABCMeta)
class AbstractPlacerAlgorithm(object):
    """ An abstract algorithm that can place a subgraph
    """
    
    @abstractmethod
    def place(self, subgraph, machine):
        """ Place a subgraph so that each subvertex is placed on a core
            
        :param subgraph: The subgraph to place
        :type subgraph: :py:class:`pacman.model.subgraph.subgraph.Subgraph`
        :param machine: The machine on which to place the graph
        :type machine: :py:class:`pacman.model.machine.machine.Machine`
        :return: A set of placements
        :rtype: :py:class:`pacman.model.placements.placements.Placements`
        :raise pacman.exceptions.PacmanPlaceException: If something\
                   goes wrong with the placement
        """
        pass
