from pacman.structures.machine import SDRAM

__author__ = 'daviess'

from pacman.structures.machine.processor import Processor
from pacman.structures.machine.router import Router
from pacman.exceptions import ProcessorAlreadyExistsException


class Chip(object):
    """ Creates a new SpiNNaker chip object """

    def __init__(self, x, y, processors=None, router=None, sdram=None, ethernet=None):
        """

        :param x: the x coordinate of the chip's position in\
               the two-dimentional grid of SpiNNaker chips
        :param y: the y coordinate of the chip's position in\
               the two-dimentional grid of SpiNNaker chips
        :param processors: a list of SpiNNaker processor objects
        :param router: a router object
        :param sdram: a memory object
        :param ethernet: the IP address of the chip or None if no ethernet attached
        :type x: int
        :type y: int
        :type processors: None or list of pacman.machine.chip.Processor
        :type router: None or pacman.machine.chip.Router
        :type sdram: None or pacman.machine.chip.SDRAM
        :type ethernet: None or str representing an IP address
        :return: a SpiNNaker chip object
        :rtype: pacman.machine.chip.Chip
        :raise None: does not raise any known exceptions
        """
        self._x = x
        self._y = y
        self._p = dict()
        self._router = router
        self._sdram = sdram
        self._ethernet = ethernet

        if processors is not None:
            self.add_processors(processors)

    def add_processor(self, processor):
        """
        Adds a working processor to the chip

        :param processor: the processor to be added to the chip
        :type processor: pacman.machine.chip.Processor
        :return: None
        :rtype: None
        :raise ProcessorAlreadyExistsException: when a processor that is\
        being added already exists in the machine
        """
        if isinstance(processor, Processor):
            if self.does_processor_exist_at_id(processor._id):
                raise ProcessorAlreadyExistsException
            else:
                self._p[processor.__repr__()] = processor

    def add_processors(self, processors):
        """
        Adds a collection of working processor objects to the chip

        :param processors: the list of processor objects to be added to the chip
        :type processors: list of pacman.machine.chip.Processor
        :return: None
        :rtype: None
        :raise None: does not raise any known exceptions
        """
        if processors is not None:
            for next_processor in processors:
                self.add_processor(next_processor)

    def add_router(self, router):
        """
        Adds a router to the chip

        :param router: the router object to be added to the chip
        :type router: pacman.machine.chip.Router
        :return: None
        :rtype: None
        :raise None: does not raise any known exceptions
        """
        if isinstance(router, Router):
            self._router = router

    def add_SDRAM(self, sdram):
        """
        Adds an SDRAM memory object to the chip

        :param sdram: the SDRAM object to be added to the chip
        :type sdram: pacman.machine.chip.SDRAM
        :return: None
        :rtype: None
        :raise None: does not raise any known exceptions
        """
        if isinstance(sdram, SDRAM):
            self._sdram = sdram

    def add_ethernet(self, ip_address=None):
        """
        Adds an ethernet object to the chip with a particular IP address

        :param ip_address: The ip address of the ethernet-attached chip
        :type ip_address: None or str
        :return: None
        :rtype: None
        :raise None: does not raise any known exceptions
        """
        if isinstance(ip_address, str):
            self._ethernet = ip_address

    def does_processor_exist_at_id(self, id):
        """
        Returns True or False based on the existence of the\
        specified processor in the chip

        :param id: the processor id to check for
        :type id: int
        :return: True or False based on the existence of the processor
        :rtype: boolean
        :raise None: does not raise any known exceptions
        """
        temp_processor = Processor(id)
        return temp_processor.__repr__() in self._p

    def get_processor_at_id(self, id):
        """
        Returns the processor with the specified is or\
        None if the processor does not exist

        :param id: the processor to return
        :type id: int
        :return: the processor with the specified id
        :rtype: pacman.machine.processor.Processor or None
        :raise None: does not raise any known exceptions
        """
        temp_processor = Processor(id)
        processor_repr = temp_processor.__repr__()
        if processor_repr in self._p:
            return self._p[processor_repr]
        else:
            return None

    @property
    def location(self):
        """
        Returns the location of the chip as a dictionary containing two\
        keys "x" and "y" associated with two integer numbers representing\
        the location of the chip in the two-dimensional grid of SpiNNaker chips

        :return: a dictionary containing two keys "x" and "y" associated\
        with two integer numbers representing the location of the chip in\
        the two-dimensional grid of SpiNNaker chips
        :rtype: {"x": int, "y": int}
        :raise None: does not raise any known exceptions
        """
        temp = dict()
        temp["x"] = self._x
        semp["y"] = self._y
        return temp

    @property
    def x(self):
        """
        Returns an integer representing the x location of the chip in\
        the two-dimensional grid of SpiNNaker chips

        :return: the x position of the chip
        :rtype: int
        :raise None: does not raise any known exceptions
        """
        return self._x

    @property
    def y(self):
        """
        Returns an integer representing the y location of the chip in\
        the two-dimensional grid of SpiNNaker chips

        :return: the y position of the chip
        :rtype: int
        :raise None: does not raise any known exceptions
        """
        return self._y

    @property
    def processors(self):
        """
        Returns a dictionary of available processors on the chip, where the key
        is the id of each processor

        :return: dictionary of available processors
        :rtype: dict of pacman.machine.chip.Processor with set of\
        keys equal to each of the processor id
        :raise None: does not raise any known exceptions
        """
        return self._p

    @property
    def router(self):
        """
        Returns the router object associated with the chip

        :return: router object associated with the chip
        :rtype: pacman.machine.chip.Router
        :raise None: does not raise any known exceptions
        """
        return self._router

    @property
    def SDRAM(self):
        """
        Returns the SDRAM object associated with the chip

        :return: SDRAM object associated with the chip
        :rtype: pacman.machine.chip.SDRAM
        :raise None: does not raise any known exceptions
        """
        return self._sdram

    @property
    def ethernet(self):
        """
        Returns the IP address of the chip, or None in case the chip\
        is not connected

        :return: IP address of the chip, or None
        :rtype: str or None
        :raise None: does not raise any known exceptions
        """
        return self._ethernet

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "{}:{}".format(self._x, self._y)