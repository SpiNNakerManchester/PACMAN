from .abstract_key_allocator_constraint import AbstractKeyAllocatorConstraint


class FlexiKeyFieldConstraint(AbstractKeyAllocatorConstraint):
    """ Constraint that indicates fields in the mask without a specific size\
        or position
    """

    __slots__ = [
        # any fields that define regions in the mask with further limitations
        "_fields"
    ]

    def __init__(self, fields):
        self._fields = fields

    @property
    def fields(self):
        return self._fields

    def __eq__(self, other):
        if not isinstance(other, FlexiKeyFieldConstraint):
            return False
        if len(self._fields) != len(other.fields):
            return False
        return all(field in other.fields for field in self._fields)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(frozenset(self._fields))

    def __repr__(self):
        return "FlexiKeyFieldConstraint(fields={})".format(
            self._fields)
