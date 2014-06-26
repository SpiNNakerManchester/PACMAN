__author__ = 'daviess'


class SDRAM(object):
    """ Creates a new SDRAM memory object with the specified size"""

    def __init__(self, size=134217728):
        """

        :param size: size in bytes of the SDRAM
        :type size: int
        :return: None
        :rtype: None
        :raise None: does not raise any known exceptions
        """
        self._memory_size = size
        pass

    @property
    def memory_size(self):
        """
        Returns the size of SDRAM in bytes

        :return: the size of SDRAM in bytes
        :rtype: int
        :raise None: does not raise any known exceptions
        """
        return self._memory_size

    @memory_size.setter
    def memory_size(self, size):
        """
        Set the size of SDRAM to the appropriate value in bytes

        :type size: int
        :return: None
        :rtype: None
        :raise None: does not raise any known exceptions
        """
        self._memory_size = size
