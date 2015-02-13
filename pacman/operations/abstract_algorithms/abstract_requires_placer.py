from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass

from pacman import exceptions
from pacman.operations.abstract_algorithms.abstract_placer_algorithm import \
    AbstractPlacerAlgorithm


@add_metaclass(ABCMeta)
class AbstractRequiresPlacer(object):

    def __init__(self):
        self._placer_algorithm = None

    def set_placer_algorithm(self, placer_algorithm):
        """ setter method for setting the placer algorithm

        :param placer_algorithm: the new placer algorithm
        :type placer_algorithm: instance of \
pacman.operations.placer_algorithms.abstract_placer_algorithm.AbstractPlacerAlgorithm

        :return: None
        :rtype: None
        :raise PacmanConfigurationException: if the placer_algorithm is not a\
        implementation of \
pacman.operations.placer_algorithms.abstract_placer_algorithm.AbstractPlacerAlgorithm

        """
        if isinstance(placer_algorithm, AbstractPlacerAlgorithm):
            self._placer_algorithm = placer_algorithm
        else:
            raise exceptions.PacmanConfigurationException(
                "The placer algorithm submitted is not a recognised placer "
                "algorithm")

    @abstractmethod
    def requires_placer(self):
        """ helper method for isinstance

        :return:
        """