

class Field(object):
    """
    field object used primiarilly at the field constraint for key allocation
    """

    def __init__(self, lo, hi, mask):
        self._lo = lo
        self._hi = hi
        self._mask = mask

    @property
    def lo(self):
        return self._lo

    @property
    def hi(self):
        return self._hi

    @property
    def mask(self):
        return self._mask

    def __repr__(self):
        return "Field with ranges {}:{} and mask {}"\
            .format(self.lo, self.hi, self.mask)

    def __str__(self):
        return self.__repr__()

    def __hash__(self):
        return (self._lo, self._hi, self._mask).__hash__()

    def __eq__(self, other_field):
        if not isinstance(other_field, Field):
            return False
        else:
            return (self._lo == other_field.lo and self._hi == other_field.hi
                    and self._mask == other_field.mask)
