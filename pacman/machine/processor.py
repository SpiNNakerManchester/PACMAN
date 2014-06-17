__author__ = 'daviess'


class Processor(object):
    """ A processor object included in a SpiNNaker chip """

    def __init__(self, id):
        """

        :param id: id of the processor in the chip
        :type id: int
        :return: a SpiNNaker chip object
        :rtype: pacman.machine.chip.Processor
        :raises None: does not raise any known exceptions
        """
        pass

    @property
    def id(self):
        """
        Returns the id of the processor

        :return: id of the processor
        :rtype: int
        :raises None: does not raise any known exceptions
        """
        pass


