from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass

import logging
from pacman.model.constraints.tag_allocator_constraints.abstract_tag_allocator_constraint import \
    AbstractTagAllocatorConstraint
from pacman.utilities import utility_calls

logger = logging.getLogger(__name__)


@add_metaclass(ABCMeta)
class AbstractTagAllocatorAlgorithm(object):

    def __init__(self, machine):
        self._machine = machine
        self._supported_constraints = list()

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

    @abstractmethod
    def locate_board_for(self, taggable_constraint, placement_tracker):
        """ method that a placer can call to deduce the board address of a
         taggablely constraitned partitioned vertex.

        :param taggable_constraint: the taggable constraint
        :param placement_tracker: the placement tracker used by the placer
        :return: a board address which this constraint can satisfy
        """

    def _locate_all_seperate_ethernet_connections(self):
        """helper method which locates all the ethernet ipadsresses for a machine

        :return: a list of ethernet ip addresses
        """
        tags = dict()
        ethernet_connected_chips = self._machine.ethernet_connected_chips
        for ethernet_connected_chip in ethernet_connected_chips:
            if ethernet_connected_chip.ip_address is not None:
                if ethernet_connected_chip.ip_address not in tags.keys():
                    tags[ethernet_connected_chip.ip_address] = set()
                    for tag in ethernet_connected_chip.tag_ids:
                        tags[ethernet_connected_chip.ip_address].add(tag)
        return tags

    def _check_algorithum_supported_constraints(self, placements):
        """ helper method to check that the algorithum can handle all the
        constraitns on these placements given the supportted constraints

        :param placements:
        :return:
        """
        subverts = list()
        for placement in placements.placements:
            subverts.append(placement.subvertex)
        utility_calls.check_algorithm_can_support_constraints(
            subverts, self._supported_constraints,
            AbstractTagAllocatorConstraint)