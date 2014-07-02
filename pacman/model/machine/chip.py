from collections import OrderedDict
from pacman.exceptions import PacmanAlreadyExistsException

class Chip(object):
    """ Represents a chip with a number of cores, an amount of SDRAM shared
        between the cores, and a router
    """

    def __init__(self, x, y, processors, router, sdram, ip_address=None):
        """

        :param x: the x-coordinate of the chip's position in the\
                    two-dimentional grid of chips
        :type x: int
        :param y: the y-coordinate of the chip's position in the\
                    two-dimentional grid of chips
        :type y: int
        :param processors: an iterable of processor objects
        :type processors: iterable of\
                    :py:class:`pacman.model.machine.processor.Processor`
        :param router: a router for the chip
        :type router: :py:class:`pacman.model.machine.router.Router`
        :param sdram: an SDRAM for the chip
        :type sdram: :py:class:`pacman.model.machine.sdram.SDRAM`
        :param ip_address: the IP address of the chip or None if no ethernet\
                    attached
        :type ip_address: str
        :raise pacman.exceptions.PacmanAlreadyExistsException: If processors\
                      contains any two processors with the same processor_id 
        """
        self._x = x
        self._y = y
        self._p = OrderedDict()
        for processor in sorted(processors, key=lambda x: x.processor_id):
            if processor.processor_id in self._p:
                raise PacmanAlreadyExistsException("processor", 
                        processor.processor_id)
            self._p[processor.processor_id] = processor
        self._router = router
        self._sdram = sdram
        self._ip_address = ip_address

    def is_processor_with_id(self, processor_id):
        """ Determines if a processor with the given id exists in the chip

        :param processor_id: the processor id to check for
        :type processor_id: int
        :return: True or False based on the existence of the processor
        :rtype: bool
        :raise None: does not raise any known exceptions
        """
        return processor_id in self._p

    def get_processor_with_id(self, processor_id):
        """ Return the processor with the specified id or None if the processor\
            does not exist

        :param processor_id: the id of the processor to return
        :type processor_id: int
        :return: the processor with the specified id or None if no such\
                    processor
        :rtype: :py:class:`pacman.model.machine.processor.Processor`
        :raise None: does not raise any known exceptions
        """
        if processor_id in self._p:
            return self._p[processor_id]
        return None

    @property
    def x(self):
        """ The x-coordinate of the chip in the two-dimensional grid of chips

        :return: the x-coordinate of the chip
        :rtype: int
        :raise None: does not raise any known exceptions
        """
        return self._x

    @property
    def y(self):
        """ The y-coordinate of the chip in the two-dimensional grid of chips

        :return: the y-coordinate of the chip
        :rtype: int
        :raise None: does not raise any known exceptions
        """
        return self._y

    @property
    def processors(self):
        """ An iterable of available processors

        :return: iterable of processors
        :rtype: iterable of :py:class:pacman.model.machine.processor.Processor`
        :raise None: does not raise any known exceptions
        """
        return self._p.itervalues()

    @property
    def router(self):
        """ The router object associated with the chip

        :return: router associated with the chip
        :rtype: :py:class:`pacman.model.machine.router.Router`
        :raise None: does not raise any known exceptions
        """
        return self._router

    @property
    def sdram(self):
        """ The sdram associated with the chip

        :return: sdram associated with the chip
        :rtype: :py:class:`pacman.model.machine.sdram.SDRAM`
        :raise None: does not raise any known exceptions
        """
        return self._sdram

    @property
    def ip_address(self):
        """ The IP address of the chip

        :return: IP address of the chip, or None if there is no ethernet\
                    connected to the chip
        :rtype: str
        :raise None: does not raise any known exceptions
        """
        return self._ip_address
