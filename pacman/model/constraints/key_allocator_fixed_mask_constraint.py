from pacman.exceptions import PacmanInvalidParameterException
from pacman.model.constraints.abstract_key_allocator_constraint \
    import AbstractKeyAllocatorConstraint


class KeyAllocatorFixedMaskConstraint(AbstractKeyAllocatorConstraint):
    """ A key allocator that fixes the mask to be assigned to a partitioned\
        edge
    """

    def __init__(self, mask, fields=None):
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
        AbstractKeyAllocatorConstraint.__init__(
            self, "key allocator constraint where subedges coming from the "
                  "vertex requires a specific mask")
        self._mask = mask
        self._fields = None
        if fields is not None:
            for field in fields:
                if field.mask & mask != field.mask:
                    raise PacmanInvalidParameterException(
                        "The field mask {} is outside of the mask {}"
                        .format(field.mask, mask))
                for other_field in fields:
                    if (other_field != field and
                            other_field.mask & field.mask != 0):
                        raise PacmanInvalidParameterException(
                            "Field masks {} and {} overlap".format(
                                field.mask, other_field.mask))
            self._fields = sorted(fields, key=lambda field: field.mask,
                                  reverse=True)

    def is_key_allocator_constraint(self):
        return True

    @property
    def mask(self):
        """ The mask to be used

        :return: The mask to be used
        :rtype: int
        """
        return self._mask

    @property
    def fields(self):
        """ Any fields in the mask - i.e. ranges of the mask that have\
            further limitations

        :return: Iterable of fields, ordered by mask with the highest bit\
                    range first
        :rtype: iterable of :py:class:`pacman.utilities.field.Field`
        """
        return self._fields
