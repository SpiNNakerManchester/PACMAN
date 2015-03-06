from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass


@add_metaclass(ABCMeta)
class AbstractPlacerAlgorithm(object):
    """ An abstract algorithm that can place a partitioned_graph
    """
    def __init__(self):
        """
        """
        self._supported_constraints = list()

    @abstractmethod
    def place(self, subgraph, machine):
        """ Place a partitioned_graph so that each subvertex is placed on a\
            core

        :param subgraph: The partitioned_graph to place
        :type subgraph: :py:class:`pacman.model.subgraph.subgraph.Subgraph`
        :param machine: The machine on which to place the partitionable_graph
        :type machine: :py:class:`spinn_machine.machine.Machine`
        :return: A set of placements
        :rtype: :py:class:`pacman.model.placements.placements.Placements`
        :raise pacman.exceptions.PacmanPlaceException: If something\
                   goes wrong with the placement
        """
        pass
