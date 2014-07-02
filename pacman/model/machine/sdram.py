class SDRAM(object):
    """ Represents the properties of the SDRAM of a chip in the machine
    """

    def __init__(self, size):
        """

        :param size: size of the SDRAM in bytes
        :type size: int
        :raise None: does not raise any known exceptions
        """
        self._size = size

    @property
    def size(self):
        """ The size of SDRAM in bytes

        :return: The size of SDRAM in bytes
        :rtype: int
        :raise None: does not raise any known exceptions
        """
        return self._size
