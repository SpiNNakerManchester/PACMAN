__author__ = 'daviess'

class Machine(object):
    """ a machine object """

    def __init__(self, chips):
        """ Create a SpiNNaker machine object
        :param chips: a collection of usable chip objects
        :type chips: iterable chip object
        :return: a new machine object
        :rtype: pacman.machine.machine.Machine
        :raises None: does not raise any known exceptions
        """
        pass

    def add_chip(self, chip):
        """
        Add an usable SpiNNaker chip object to the machine object
        :param chip: a usable SpiNNaker chip object
        :type chip: pacman.machine.chip.Chip
        :return: None
        :rtype: None
        :raises None: does not raise any known exceptions
        """
        pass

    def add_chips(self, chips):
        """
        Add a collection of usable SpiNNaker chip object to the machine object
        :param chips: a collection of usable SpiNNaker chip object
        :type chips: iterable object
        :return: None
        :rtype: None
        :raises None: does not raise any known exceptions
        """
        pass

    @property
    def chips(self):
        """
        Returns the chips allocated to the machine object
        :return: a collection of chip objects
        :rtype: iterable chip object
        :raises None: does not raise any known exceptions
        """
