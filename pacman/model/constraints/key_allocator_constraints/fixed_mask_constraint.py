from .abstract_key_allocator_constraint import AbstractKeyAllocatorConstraint


class FixedMaskConstraint(AbstractKeyAllocatorConstraint):
    """ A key allocator that fixes the mask to be assigned to an edge.
    """

    __slots__ = [
        # the mask to be used during key allocation
        "_mask"
    ]

    def __init__(self, mask):
        """
        :param mask: the mask to be used during key allocation
        :type mask: int
        """
        self._mask = mask

    @property
    def mask(self):
        """ The mask to be used

        :return: The mask to be used
        :rtype: int
        """
        return self._mask

    def __eq__(self, other):
        if not isinstance(other, FixedMaskConstraint):
            return False
        return self._mask == other.mask

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._mask)

    def __repr__(self):
        return "FixedMaskConstraint(mask={})".format(self._mask)
