from pacman.model.constraints.abstract_key_allocator_constraint \
    import AbstractKeyAllocatorConstraint


class KeyAllocatorFixedNKeysConstraint(AbstractKeyAllocatorConstraint):
    """ A constraint that says that the keys allocated to a given partitioned\
        edge should be the same as the keys allocated to another partitioned\
        edge
    """
    def __init__(self, n_keys):
        AbstractKeyAllocatorConstraint.__init__(
            self, "fixed_n_keys_constraint with fixed_nkeys of {}"
                  .format(n_keys))
        self._n_keys = n_keys

    @property
    def n_keys(self):
        return self._n_keys

    def is_key_allocator_constraint(self):
        return True