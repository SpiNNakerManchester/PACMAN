from abc import abstractproperty
from abc import abstractmethod

from pacman.model.graphs.abstract_vertex import AbstractVertex


class AbstractVirtualVertex(AbstractVertex):
    """ A vertex which exists outside of the machine
    """

    __slots__ = ()

    @abstractproperty
    def board_address(self):
        """ The IP address of the board to which the device is connected,\
            or None for the boot board

        :rtype: str
        """

    @abstractmethod
    def set_virtual_chip_coordinates(self, virtual_chip_x, virtual_chip_y):
        """ Set the details of the virtual chip that has been added to the\
            machine for this vertex

        :param virtual_chip_x: The x-coordinate of the added chip
        :param virtual_chip_y: The y-coordinate of the added chip
        """

    @abstractproperty
    def virtual_chip_x(self):
        """ The x-coordinate of the virtual chip where this vertex is to be\
            placed

            :rtype: int
        """

    @abstractproperty
    def virtual_chip_y(self):
        """ The y-coordinate of the virtual chip where this vertex is to be\
            placed

            :rtype: int
        """
