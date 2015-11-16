from pacman.utilities.utility_objs.flexi_field import SUPPORTED_TAGS


class Field(object):
    """
    field object used primiarilly at the field constraint for key allocation
    """

    def __init__(self, lo, hi, value, tag=SUPPORTED_TAGS.ROUTING):
        self._lo = lo
        self._hi = hi
        self._value = value
        self._tag = tag

    @property
    def lo(self):
        return self._lo

    @property
    def hi(self):
        return self._hi

    @property
    def value(self):
        return self._value

    @property
    def tag(self):
        return self._tag

    def __repr__(self):
        return "Field with ranges {}:{} and value {} and tag {}"\
            .format(self.lo, self.hi, self.value, self._value)

    def __str__(self):
        return self.__repr__()

    def __hash__(self):
        return (self._lo, self._hi, self._value, self._tag).__hash__()

    def __eq__(self, other_field):
        if not isinstance(other_field, Field):
            return False
        else:
            return (self._lo == other_field.lo and self._hi == other_field.hi
                    and self._value == other_field.value
                    and self._tag == other_field.tag)
