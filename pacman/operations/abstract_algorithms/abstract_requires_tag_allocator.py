from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass
from pacman import exceptions
from pacman.operations.abstract_algorithms.abstract_tag_allocator_algorithm\
    import AbstractTagAllocatorAlgorithm


@add_metaclass(ABCMeta)
class AbstractRequiresTagAllocator(object):

    def __init__(self):
        self._tag_allcoator = None

    def set_tag_allocator(self, tag_allocator_algorithum):
        """ setter method for setting the placer algorithm

        :param tag_allocator_algorithum: the new placer algorithm
        :type tag_allocator_algorithum: istance of \
pacman.operations.abstract_algorithms.abstract_tag_allocator_algorithm.AbstractTagAllocatorAlgorithm
        :return: None
        :rtype: None
        :raise PacmanConfigurationException: if the tag_allocator_algorithm is not a\
        implementation of \
pacman.operations.abstract_algorithms.abstract_tag_allocator_algorithm.AbstractTagAllocatorAlgorithm

        """
        if isinstance(tag_allocator_algorithum, AbstractTagAllocatorAlgorithm):
            self._tag_allcoator = tag_allocator_algorithum
        else:
            raise exceptions.PacmanConfigurationException(
                "The placer algorithm submitted is not a recognised placer "
                "algorithm")

    @abstractmethod
    def requires_tag_allocator(self):
        """ helper emthod for isinstance

        :return:
        """