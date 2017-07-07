from .abstract_key_allocator_constraint import AbstractKeyAllocatorConstraint


class ContiguousKeyRangeContraint(AbstractKeyAllocatorConstraint):
    """ Key allocator constraint that keeps the keys allocated to a contiguous\
        range.  Without this constraint, keys can be allocated across the key\
        space.
    """

    __slots__ = []

    def __eq__(self, other):
        return isinstance(other, ContiguousKeyRangeContraint)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash("ContiguousKeyRangeContraint")

    def __repr__(self):
        return "KeyAllocatorContiguousRangeConstraint()"
