from pacman.model.constraints.abstract_key_allocator_constraint \
    import AbstractKeyAllocatorConstraint


class KeyAllocatorContiguousRangeContraint(AbstractKeyAllocatorConstraint):
    """ Key allocator constraint that keeps the keys allocated to a contiguous\
        range.  Without this constraint, keys can be allocated across the key\
        space.
    """

    def __init__(self):
        AbstractKeyAllocatorConstraint.__init__(
            self, "Key allocator constraint to ensure that keys are not split")
