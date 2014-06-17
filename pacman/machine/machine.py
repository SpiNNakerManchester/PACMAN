__author__ = 'daviess'


class Machine(object):
    """ Creates a SpiNNaker machine object """

    def __init__(self, chips):
        """
        :param chips: a list of usable chip objects
        :type chips: list of pacman.machine.chip.Chip
        :return: a new machine object
        :rtype: pacman.machine.machine.Machine
        :raises None: does not raise any known exceptions
        """
        pass

    def add_chip(self, chip):
        """
        Adds an usable SpiNNaker chip object to the machine object
        :param chip: a usable SpiNNaker chip object
        :type chip: pacman.machine.chip.Chip
        :return: None
        :rtype: None
        :raises None: does not raise any known exceptions
        """
        pass

    def add_chips(self, chips):
        """
        Adds a list of usable SpiNNaker chip object to the machine object
        :param chips: a list of usable chip objects
        :type chips: list of pacman.machine.chip.Chip
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
