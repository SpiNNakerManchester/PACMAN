__author__ = 'daviess'

class Chip(object):
    """ a SpiNNaker chip object """

    def __init__(self, processors=None, router=None, sdram=None):
        """
        Creates a SpiNNaker chip object
        :param processors: a collection of SpiNNaker processor objects
        :param router: a router object
        :param sdram: a memory object
        :type processors: None or iterable object
        :type router: None or pacman.machine.chip.Router
        :type sdram: None or pacman.machine.chip.SDRAM
        :return: a SpiNNaker chip object
        :rtype: pacman.machine.chip.Chip
        :raises None: does not raise any known exceptions
        """
        pass

class Router(object):
    """ a router object """

class SDRAM(object):
    """ a SDRAM memory object """