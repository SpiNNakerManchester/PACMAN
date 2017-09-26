from pacman.exceptions import PacmanConfigurationException
import numpy


class BaseKeyAndMask(object):
    """ A Key and Mask to be used for routing
    """

    __slots__ = [
        # The routing key
        "_base_key",

        # The routing mask
        "_mask"
    ]

    def __init__(self, base_key, mask):
        """

        :param base_key: The routing key
        :type base_key: int
        :param mask: The routing mask
        :type mask: int
        :raise PacmanConfigurationException: If key & mask != key i.e. the key\
                    is not valid for the given mask
        """
        self._base_key = base_key
        self._mask = mask

        if base_key & mask != base_key:
            raise PacmanConfigurationException(
                "This routing info is invalid as the mask and key together "
                "alters the key. This is deemed to be a error from "
                "spynnaker's point of view and therefore please rectify and"
                "try again")

    @property
    def key(self):
        """ The base key

        :return: The base key
        :rtype: int
        """
        return self._base_key

    @property
    def key_combo(self):
        """ The key combined with the mask
        """
        return self._base_key & self._mask

    @property
    def mask(self):
        """ The mask

        :return: The mask
        :rtype: int
        """
        return self._mask

    def __eq__(self, key_and_mask):
        if not isinstance(key_and_mask, BaseKeyAndMask):
            return False
        else:
            return (self._base_key == key_and_mask.key and
                    self._mask == key_and_mask.mask)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return "KeyAndMask:{}:{}".format(hex(self._base_key), hex(self._mask))

    def __str__(self):
        return self.__repr__()

    def __hash__(self):
        return self.__repr__().__hash__()

    @property
    def n_keys(self):
        """ The total number of keys that can be generated given the mask

        :return: The number of keys
        :rtype: int
        """
        # converts mask into array of bit representation
        unwrapped_mask = numpy.unpackbits(
            numpy.asarray([self._mask], dtype=">u4").view(dtype="uint8"))

        # how many zeros are in the bit representation array
        zeros = numpy.where(unwrapped_mask == 0)[0]

        # number of keys available from this mask size
        return 2 ** len(zeros)

    def get_keys(self, key_array=None, offset=0, n_keys=None):
        """ Get the ordered list of keys that the combination allows

        :param key_array: Optional array into which the returned keys will be\
                    placed
        :type key_array: array-like of int
        :param offset: Optional offset into the array at which to start\
                    placing keys
        :type offset: int
        :param n_keys: Optional limit on the number of keys returned.  If less\
                    than this number of keys are available, only the keys\
                    available will be added
        :type n_keys: int
        :return: A tuple of an array of keys and the number of keys added to\
                    the array
        :rtype: (array-like of int, int)
        """
        # Get the position of the zeros in the mask - assume 32-bits
        unwrapped_mask = numpy.unpackbits(
            numpy.asarray([self._mask], dtype=">u4").view(dtype="uint8"))
        zeros = numpy.where(unwrapped_mask == 0)[0]

        # If there are no zeros, there is only one key in the range, so
        # return that
        if len(zeros) == 0:
            if key_array is None:
                key_array = numpy.zeros(1, dtype=">u4")
            key_array[offset] = self._base_key
            return key_array, 1

        # We now know how many values there are - 2^len(zeros)
        max_n_keys = 2 ** len(zeros)
        if key_array is not None and len(key_array) < max_n_keys:
            max_n_keys = len(key_array)
        if n_keys is None or n_keys > max_n_keys:
            n_keys = max_n_keys
        if key_array is None:
            key_array = numpy.zeros(n_keys, dtype=">u4")

        # Create a list of 2^len(zeros) keys
        unwrapped_key = numpy.unpackbits(
            numpy.asarray([self._base_key], dtype=">u4").view(dtype="uint8"))

        # for each key, create its key with the idea of a neuron id being
        # continuous and live at an offset position from the bottom of
        # the key
        for value in range(n_keys):
            key = numpy.copy(unwrapped_key)
            unwrapped_value = numpy.unpackbits(
                numpy.asarray([value], dtype=">u4")
                     .view(dtype="uint8"))[-len(zeros):]
            key[zeros] = unwrapped_value
            key_array[value + offset] = \
                numpy.packbits(key).view(dtype=">u4")[0].item()
        return key_array, n_keys
