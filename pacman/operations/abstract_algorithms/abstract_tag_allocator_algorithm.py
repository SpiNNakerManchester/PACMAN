from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass

import logging
logger = logging.getLogger(__name__)


@add_metaclass(ABCMeta)
class AbstractTagAllocatorAlgorithm(object):

    def __init__(self, machine):
        self._machine = machine

    @abstractmethod
    def is_tag_allocator(self):
        """ helper method for is_instance

        :return:
        """

    @abstractmethod
    def allocate(self, placements):
        """ main method for allcoating tags

        :param placements:
        :return:
        """


    def _locate_all_seperate_ethernet_connections(self):
        """helper method which locates all the ethernet ipadsresses for a machine

        :return: a list of ethernet ip addresses
        """
        tags = dict()
        ethernet_connected_chips = self._machine.ethernet_connected_chips
        for ethernet_connected_chip in ethernet_connected_chips:
            if ethernet_connected_chip.ip_address not in tags.keys():
                tags[ethernet_connected_chip.ip_address] = \
                    ethernet_connected_chip.tag_ids
        return tags