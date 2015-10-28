from pacman.model.constraints.abstract_constraints.\
    abstract_key_allocator_constraint \
    import AbstractKeyAllocatorConstraint


class KeyAllocatorFixedFieldConstraint(AbstractKeyAllocatorConstraint):
    """ A key allocator that fixes the mask to be assigned to a partitioned\
        edge
    """

    def __init__(self, fields=None):
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

        self._fields = sorted(fields, key=lambda field: field.mask,
                              reverse=True)

    def is_key_allocator_constraint(self):
        """
        helper method for isinstance
        :return:
        """
        return True

    @property
    def fields(self):
        """ Any fields in the mask - i.e. ranges of the mask that have\
            further limitations

        :return: Iterable of fields, ordered by mask with the highest bit\
                    range first
        :rtype: iterable of :py:class:`pacman.utilities.field.Field`
        """
        return self._fields

    def __eq__(self, other):
        if not isinstance(other, KeyAllocatorFixedFieldConstraint):
            return False
        else:
            if len(self._fields) != len(other.fields):
                return False
            else:
                for field in self._fields:
                    if field not in other.fields:
                        return False
                return True

    def __hash__(self):
        frozen_fields = frozenset(self._fields)
        return hash(frozen_fields)



