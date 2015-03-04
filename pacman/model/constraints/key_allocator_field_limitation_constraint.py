from pacman.model.constraints.abstract_key_allocator_constraint import \
    AbstractKeyAllocatorConstraint


class KeyAllocatorFieldLimitationConstraint(AbstractKeyAllocatorConstraint):

    def __init__(self, fields):
            AbstractKeyAllocatorConstraint.__init__(
                self, "field limitation constraint with fields {}"
                      .format(fields))
            self._fields = fields

    def is_key_allocator_constraint(self):
        return True

    @property
    def fields(self):
        return self._fields