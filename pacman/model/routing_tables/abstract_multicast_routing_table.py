from six import add_metaclass
from spinn_utilities.abstract_base import AbstractBase, abstractproperty, \
    abstractmethod


@add_metaclass(AbstractBase)
class AbsractMulticastRoutingTable(object):

    @abstractproperty
    def x(self):
        """The x-coordinate of the chip of this table

        :return: The x-coordinate
        :rtype: int
        """

    @abstractproperty
    def y(self):
        """ The y-coordinate of the chip of this table

        :return: The y-coordinate
        :rtype: int
        """

    @abstractproperty
    def multicast_routing_entries(self):
        """ The multicast routing entries in the table

        :return: an iterable of multicast routing entries
        :rtype: iterable(:py:class:`spinn_machine.MulticastRoutingEntry`)
        :raise None: does not raise any known exceptions
        """

    @abstractproperty
    def number_of_entries(self):
        """ The number of multi-cast routing entries there are in the\
            multicast routing table

        :return: int
        """

    @abstractproperty
    def number_of_defaultable_entries(self):
        """ The number of multi-cast routing entries that are set to be\
            defaultable within this multicast routing table

        :return: int
        """

    @abstractmethod
    def __eq__(self, other):
        """equals method"""

    @abstractmethod
    def __ne__(self, other):
        """ not equals method"""

    @abstractmethod
    def __hash__(self):
        """hash"""

    @abstractmethod
    def __repr__(self):
        """repr"""
