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

    def get_chip_at_location_xy(self, x, y):
        """
        Returns the SpiNNaker chip at a specific (x, y) location

        :param x: the x coordinate of the requested chip
        :param y: the y coordinate of the requested chip
        :type x: int
        :type y: int
        :return: the chip at the specified location
        :rtype: pacman.machine.chip.Chip or None
        :raises None: does not raise any known exceptions
        """
        pass

    def get_chip_at_location(self, location):
        """
        Returns the SpiNNaker chip at a specific (x, y) location\
        where the coordinates are expressed in a dictionary with\
        two keys

        :param location: the x coordinate of the requested chip
        :type location: {"x": int, "y": int}
        :return: the chip at the specified location
        :rtype: pacman.machine.chip.Chip or None
        :raises None: does not raise any known exceptions
        """
        pass
