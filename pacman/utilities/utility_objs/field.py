from pacman.utilities.utility_objs.flexi_field import SUPPORTED_TAGS
import uuid


class Field(object):
    """
    field object used primiarilly at the field constraint for key allocation
    """

    def __init__(self, lo, hi, value, tag=SUPPORTED_TAGS.ROUTING, name=None):
        self._lo = lo
        self._hi = hi
        self._value = value
        self._tag = tag
        if name is None:
            self._name = uuid.uuid4()
        else:
            self._name = name

    @property
    def lo(self):
        return self._lo

    @property
    def hi(self):
        return self._hi

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, new_value):
        self._name = new_value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value

    @property
    def tag(self):
        return self._tag

    @tag.setter
    def tag(self, new_value):
        self._tag = new_value

    def __repr__(self):
        return "Field with ranges {}:{} and value {} and tag {} and name {}"\
            .format(self.lo, self.hi, self.value, self._value, self._name)

    def __str__(self):
        return self.__repr__()

    def __hash__(self):
        return (self._lo, self._hi, self._value, self._tag,
                self._name).__hash__()

    def __eq__(self, other_field):
        if not isinstance(other_field, Field):
            return False
        else:
            return (self._lo == other_field.lo and self._hi == other_field.hi
                    and self._value == other_field.value
                    and self._tag == other_field.tag
                    and self._name == other_field.name)
