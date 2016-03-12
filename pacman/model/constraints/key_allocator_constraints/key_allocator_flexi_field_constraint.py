from pacman.model.constraints.abstract_constraints.\
    abstract_key_allocator_constraint import AbstractKeyAllocatorConstraint


class KeyAllocatorFlexiFieldConstraint(AbstractKeyAllocatorConstraint):
    """ Constraint that indicates fields in the mask without a specific size\
        or position
    """

    def __init__(self, fields):
        AbstractKeyAllocatorConstraint.__init__(
            self, "Key allocator constraint where subedges coming from the "
                  "partitioned_graph requires a set of fields which are "
                  "flexible in nature")
        self._fields = fields

    @property
    def fields(self):
        """

        :return:
        """
        return self._fields

    def is_key_allocator_constraint(self):
        return True

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
