from pacman.model.machine.chip import Chip
from pacman.exceptions import PacmanAlreadyExistsException
from collections import OrderedDict

def _get_chip_dict_id(self, x, y):
    """ Get the dictionary key for a given x, y chip coordinate
    
    :param x: The chip x-coordinate
    :type x: int
    :param y: The chip y-coordinate
    :type y: int
    :return: A string that can be used as a dictionary id
    :rtype: str
    """
    return "{},{}".format(x, y)


class Machine(object):
    """ A Representation of a Machine with a number of Chips
    """

    def __init__(self, chips):
        """
        :param chips: An iterable of chips in the machine
        :type chips: iterable of :py:class:`pacman.model.machine.chip.Chip`
        :raise pacman.exceptions.PacmanAlreadyExistsException: If any two\
                    chips have the same x and y coordinates
        """
        
        # The maximum chip x coordinate
        self._max_chip_x = 0
        
        # The maximum chip y coordinate
        self._max_chip_y = 0
        
        # The dictionary of chips
        self._chips = OrderedDict()
        self.add_chips(chips)

    def add_chip(self, chip):
        """ Add a chip to the machine
        
        :param chip: The chip to add to the machine
        :type chip: :py:class:`pacman.model.machine.chip.Chip`
        :return: Nothing is returned
        :rtype: None
        :raise pacman.exceptions.PacmanAlreadyExistsException: If a chip with\
                    the same x and y coordinates already exists
        """
        chip_id = _get_chip_dict_id(chip.x, chip.y)
        if chip_id in self._chips:
            raise PacmanAlreadyExistsException(
                    "chip", "{}, {}".format(chip.x, chip.y))
        
        self._chips[chip_id] = chip
        
        if chip.x > self._max_chip_x:
            self._max_chip_x = chip.x
        if chip.y > self._max_chip_y:
            self._max_chip_y = chip.y

    def add_chips(self, chips):
        """ Add some chips to the machine
        
        :param chips: an iterable of chips
        :type chips: iterable of :py:class:`pacman.model.machine.chip.Chip`
        :return: Nothing is returned
        :rtype: None
        :raise pacman.exceptions.PacmanAlreadyExistsException: If a chip with\
                    the same x and y coordinates already exists
        """
        for next_chip in chips:
            self.add_chip(next_chip)

    @property
    def chips(self):
        """ An iterable of chips in the machine

        :return: An iterable of chips
        :rtype: iterable of :py:class:`pacman.model.machine.chip.Chip`
        :raise None: does not raise any known exceptions
        """
        return self._chips

    def get_chip_at(self, x, y):
        """ Get the chip at a specific (x, y) location

        :param x: the x-coordinate of the requested chip
        :type x: int
        :param y: the y-coordinate of the requested chip
        :type y: int
        :return: the chip at the specified location, or None if no such chip
        :rtype: :py:class:`pacman.model.machine.chip.Chip`
        :raise None: does not raise any known exceptions
        """
        chip_id = _get_chip_dict_id(x, y)
        if chip_id in self._chips:
            return self._chips[chip_id]
        return None
    
    def is_chip_at(self, x, y):
        """ Determines if a chip exists at the given coordinates

        :param x: x location of the chip to test for existence
        :type x: int
        :param y: y location of the chip to test for existence
        :type y: int
        :return: True if the chip exists, False otherwise
        :rtype: bool
        :raise None: does not raise any known exceptions
        """
        chip_id = _get_chip_dict_id(x, y)
        return chip_id in self._chips
    
    @property
    def max_chip_x(self):
        """ The maximum x-coordinate of any chip in the board
        
        :return: The maximum x-coordinate
        :rtype: int
        """
        return self._max_chip_x
    
    @property
    def max_chip_y(self):
        """ The maximum y-coordinate of any chip in the board
        
        :return: The maximum y-coordinate
        :rtype: int
        """
        return self._max_chip_y
