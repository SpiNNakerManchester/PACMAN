from pacman.model.constraints.key_allocator_constraints.\
    abstract_key_allocator_constraint import AbstractKeyAllocatorConstraint


class KeyAllocatorFixedFieldConstraint(AbstractKeyAllocatorConstraint):
    """ Constraint that indicates fields in the mask of a key
    """

    __slots__ = [
        # any fields that define regions in the mask with further limitations
        "_fields"
    ]

    def __init__(self, fields=None):
        """

        :param fields: any fields that define regions in the mask with further\
                    limitations
        :type fields: iterable of :py:class:`pacman.utilities.field.Field`
        :raise PacmanInvalidParameterException: if any of the fields are\
                    outside of the mask i.e. mask & field.mask != field.mask\
                    or if any of the field masks overlap i.e.\
                    field.mask & other_field.mask != 0
        """
        self._fields = sorted(fields, key=lambda field: field.mask,
                              reverse=True)

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

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        frozen_fields = frozenset(self._fields)
        return hash(frozen_fields)

    def __repr__(self):
        return "KeyAllocatorFixedFieldConstraint(fields={})".format(
            self._fields)
