__author__ = 'daviess'

from pacman.structures.machine.chip import Chip
from pacman.exceptions import ChipAlreadyExistsException


class Machine(object):
    """ Creates a SpiNNaker machine object """

    def __init__(self, dimensions, chips=None):
        """
        :param chips: a list of usable chip objects
        :param dimensions: a tuple contains the x and y dimensions of
                           the machine
        :type dimensions: dict with x and y as keys
        :type chips: list of pacman.machine.chip.Chip or None
        :return: a new machine object
        :rtype: pacman.machine.machine.Machine
        :raise None: does not raise any known exceptions
        """
        self._chips = dict()

        if chips is not None:
            self.add_chips(chips)
        #somehow detemrine machien dimenions from its inputs
        self._x_dim = dimensions['x']
        self._y_dim = dimensions['y']

    def add_chip(self, chip):
        """
        Adds an usable SpiNNaker chip object to the machine object
        :param chip: a usable SpiNNaker chip object
        :type chip: pacman.machine.chip.Chip
        :return: None
        :rtype: None
        :raise ChipAlreadyExistsException: When the chip being added already\
        exists in the machine
        """
        if isinstance(chip, Chip):
            if self.does_chip_exist_at_xy(chip.x, chip.y):
                raise ChipAlreadyExistsException
            else:
                self._chips[chip.__repr__()] = chip

    def add_chips(self, chips):
        """
        Adds a list of usable SpiNNaker chip object to the machine object
        :param chips: a list of usable chip objects
        :type chips: list of pacman.machine.chip.Chip
        :return: None
        :rtype: None
        :raise None: does not raise any known exceptions
        """
        if chips is not None:
            for next_chip in chips:
                self.add_chip(next_chip)

    @property
    def chips(self):
        """
        Returns the chips allocated to the machine object

        :return: a collection of chip objects
        :rtype: iterable chip object
        :raise None: does not raise any known exceptions
        """
        return self._chips

    def get_chip_at_xy(self, x, y):
        """
        Returns the SpiNNaker chip at a specific (x, y) location or None\
        if the chip does not exist

        :param x: the x coordinate of the requested chip
        :param y: the y coordinate of the requested chip
        :type x: int
        :type y: int
        :return: the chip at the specified location
        :rtype: pacman.machine.chip.Chip or None
        :raise None: does not raise any known exceptions
        """
        temp_chip = Chip(x, y)
        chip_repr = temp_chip.__repr__()
        if chip_repr in self._chips:
            return self._chips[chip_repr]
        else:
            return None

    def get_chip_at_location(self, location):
        """
        Returns the SpiNNaker chip at a specific (x, y) location\
        where the coordinates are expressed in a dictionary with\
        two keys or None if the chip does not exist

        :param location: the x coordinate of the requested chip
        :type location: {"x": int, "y": int}
        :return: the chip at the specified location
        :rtype: pacman.machine.chip.Chip or None
        :raise None: does not raise any known exceptions
        """
        return self.get_chip_at_xy(location["x"], location["y"])

    def does_chip_exist_at_xy(self, x, y):
        """
        Returns True or False based on the existence of the\
        specified chip in the machine

        :param x: x location of the chip to test for existence
        :param y: y location of the chip to test for existence
        :type x: int
        :type y: int
        :return: True or False based on the existence of the chip
        :rtype: boolean
        :raise None: does not raise any known exceptions
        """
        temp_chip = Chip(x, y)
        return temp_chip.__repr__() in self._chips

    def does_chip_exist_at_location(self, location):
        """
        Returns True or False based on the existence of the\
        specified chip in the machine

        :param location: the x coordinate of the requested chip
        :type location: {"x": int, "y": int}
        :return: True or False based on the existence of the chip
        :rtype: boolean
        :raise None: does not raise any known exceptions
        """
        return self.does_chip_exist_at_xy(location["x"], location["y"])

    @property
    def dimenions(self):
        """Returns a tuple containing the machines dimensions

        :return: a tuple containing the x and y dimension of the machine
        :rtype: tuple
        :raise None: does not raise any known exceptions
        """
        return {'x': self._x_dim, 'y': self._y_dim}
