from pacman.model.constraints.key_allocator_constraints.\
    abstract_key_allocator_constraint import AbstractKeyAllocatorConstraint
from pacman.model.decorators.overrides import overrides


class KeyAllocatorContiguousRangeContraint(AbstractKeyAllocatorConstraint):
    """ Key allocator constraint that keeps the keys allocated to a contiguous\
        range.  Without this constraint, keys can be allocated across the key\
        space.
    """

    def __eq__(self, other):
        if not isinstance(other, KeyAllocatorContiguousRangeContraint):
            return False
        else:
            return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash("KeyAllocatorContiguousRangeContraint")

    def __repr__(self):
        return "KeyAllocatorContiguousRangeConstraint()"

    @overrides(AbstractKeyAllocatorConstraint.label)
    def label(self):
        return "Key allocator constraint to ensure that keys are not split"
