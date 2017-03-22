from pacman.model.constraints.key_allocator_constraints.\
    abstract_key_allocator_constraint import AbstractKeyAllocatorConstraint


class KeyAllocatorFlexiFieldConstraint(AbstractKeyAllocatorConstraint):
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
        if not isinstance(other, KeyAllocatorFlexiFieldConstraint):
            return False
        else:
            for field in self._fields:
                if field not in other.fields:
                    return False
            return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(frozenset(self._fields))

    def __repr__(self):
        return "KeyAllocatorFlexiFieldConstraint(fields={})".format(
            self._fields)
