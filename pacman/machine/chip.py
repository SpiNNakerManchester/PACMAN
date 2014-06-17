__author__ = 'daviess'


class Chip(object):
    """ Creates a new SpiNNaker chip object """

    def __init__(self, location, processors=None, router=None, sdram=None, ethernet=None):
        """

        :param location: a tuple (x, y) representing the chip's position in\
               the two-dimentional grid of SpiNNaker chips
        :param processors: a list of SpiNNaker processor objects
        :param router: a router object
        :param sdram: a memory object
        :param ethernet: the IP address of the chip or None if no ethernet attached
        :type location: a tuple (x, y)
        :type processors: None or list of pacman.machine.chip.Processor
        :type router: None or pacman.machine.chip.Router
        :type sdram: None or pacman.machine.chip.SDRAM
        :type ethernet: None or str representing an IP address
        :return: a SpiNNaker chip object
        :rtype: pacman.machine.chip.Chip
        :raises None: does not raise any known exceptions
        """
        pass

    def add_processor(self, processor):
        """
        Adds a working processor to the chip

        :param processor: the processor to be added to the chip
        :type processor: pacman.machine.chip.Processor
        :return: None
        :rtype: None
        :raises None: does not raise any known exceptions
        """
        pass

    def add_processors(self, processors):
        """
        Adds a collection of working processor objects to the chip

        :param processors: the list of processor objects to be added to the chip
        :type processors: list of pacman.machine.chip.Processor
        :return: None
        :rtype: None
        :raises None: does not raise any known exceptions
        """
        pass

    def add_router(self, router):
        """
        Adds a router to the chip

        :param router: the router object to be added to the chip
        :type router: pacman.machine.chip.Router
        :return: None
        :rtype: None
        :raises None: does not raise any known exceptions
        """
        pass

    def add_SDRAM(self, SDRAM):
        """
        Adds an SDRAM memory object to the chip

        :param SDRAM: the SDRAM object to be added to the chip
        :type SDRAM: pacman.machine.chip.SDRAM
        :return: None
        :rtype: None
        :raises None: does not raise any known exceptions
        """
        pass

    def add_ethernet(self, ip_address=None):
        """
        Adds an ethernet object to the chip with a particular IP address

        :param ip_address: The ip address of the ethernet-attached chip
        :type ip_address: None or str
        :return: None
        :rtype: None
        :raises None: does not raise any known exceptions
        """
        pass

    @property
    def processors(self):
        """
        Returns the list of available processors on the chip

        :return: list of available processors
        :rtype: list of pacman.machine.chip.Processor
        :raises None: does not raise any known exceptions
        """
        pass

    @property
    def router(self):
        """
        Returns the router object associated with the chip

        :return: router object associated with the chip
        :rtype: pacman.machine.chip.Router
        :raises None: does not raise any known exceptions
        """
        pass

    @property
    def SDRAM(self):
        """
        Returns the SDRAM object associated with the chip

        :return: SDRAM object associated with the chip
        :rtype: pacman.machine.chip.SDRAM
        :raises None: does not raise any known exceptions
        """
        pass

    @property
    def ethernet(self):
        """
        Returns the IP address of the chip, or None in case the chip\
        is not connected

        :return: IP address of the chip, or None
        :rtype: str or None
        :raises None: does not raise any known exceptions
        """
        pass
