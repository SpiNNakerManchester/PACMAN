from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass

import logging

logger = logging.getLogger(__name__)


@add_metaclass(ABCMeta)
class AbstractTagAllocatorAlgorithm(object):
    """ An algorithm that allocates IP Tag and Reverse IP Tags
    """

    def __init__(self):
        self._supported_constraints = list()

    @abstractmethod
    def allocate_tags(self, machine, placements):
        """ Perform the allocation of IP tags and reverse IP tags

        :param machine: The machine on to which the tags will be placed
        :type machine: :py:class:`spinn_machine.machine.Machine`
        :param placements: The placements which require tags to be assigned
        :type placements:\
                    :py:class:`pacman.model.placements.placements.Placements`
        :return: The tags allocated
        :rtype: :py:class:`pacman.model.tags.tags.Tags`
        """
