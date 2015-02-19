from pacman.model.constraints.abstract_key_allocator_constraint \
    import AbstractKeyAllocatorConstraint


class KeyAllocatorFixedMaskConstraint(AbstractKeyAllocatorConstraint):
    """ A key allocator that fixes the mask to be assigned to a partitioned\
        edge
    """

    def __init__(self, mask):
        """

        :param mask: the mask to be used during key allocation
        :type mask: int
        :raise None: does not raise any known exceptions
        """
        AbstractKeyAllocatorConstraint.__init__(
            self, "key allocator constraint where subedges coming from the "
                  "vertex requires a specific mask")
        self._mask = mask

    def is_key_allocator_constraint(self):
        return True

    @property
    def mask(self):
        """ The mask to be used

        :return: The mask to be used
        :rtype: int
        """
        return self._mask
