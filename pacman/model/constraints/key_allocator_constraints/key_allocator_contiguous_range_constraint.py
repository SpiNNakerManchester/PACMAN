from pacman.model.constraints.abstract_constraints.abstract_key_allocator_constraint \
    import AbstractKeyAllocatorConstraint


class KeyAllocatorContiguousRangeContraint(AbstractKeyAllocatorConstraint):
    """ Key allocator constraint that keeps the keys allocated to a contiguous\
        range.  Without this constraint, keys can be allocated across the key\
        space.
    """

    def __init__(self):
        AbstractKeyAllocatorConstraint.__init__(
            self, "Key allocator constraint to ensure that keys are not split")

    def is_key_allocator_constraint(self):
        """
        helper method for instance
        :return:
        """
        return True

    def __eq__(self, other):
        """
        over load of equals so that two KeyAllocatorContiguousRangeContraints
        return True
        :param other: another constraint
        :return:
        """
        if not isinstance(other, KeyAllocatorContiguousRangeContraint):
            return False
        else:
            return True

    def __hash__(self):
        """

        :return:
        """
        return hash("Key allocator constraint to ensure "
                    "that keys are not split")
