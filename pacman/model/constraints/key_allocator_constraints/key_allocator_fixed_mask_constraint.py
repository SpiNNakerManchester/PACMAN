from pacman.model.constraints.key_allocator_constraints.\
    abstract_key_allocator_constraint import AbstractKeyAllocatorConstraint


class KeyAllocatorFixedMaskConstraint(AbstractKeyAllocatorConstraint):
    """ A key allocator that fixes the mask to be assigned to an edge
    """

    def __init__(self, mask):
        """

        :param mask: the mask to be used during key allocation
        :type mask: int
        :param fields: any fields that define regions in the mask with further\
                    limitations
        :type fields: iterable of :py:class:`pacman.utilities.field.Field`
        :raise PacmanInvalidParameterException: if any of the fields are\
                    outside of the mask i.e. mask & field.mask != field.mask\
                    or if any of the field masks overlap i.e.\
                    field.mask & other_field.mask != 0
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
        if not isinstance(other, KeyAllocatorFixedMaskConstraint):
            return False
        else:
            if self._mask == other.mask:
                return True
            else:
                return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._mask)
