from enum import Enum

SUPPORTED_TAGS = Enum(
    value="SUPPORTED_TAGS",
    names=[("APPLICATION", 0),
           ("ROUTING", 1)])


class FlexiField(object):
    """ field who's location is not fixed in key allocation

    """

    __slots__ = [
        # identifier
        "_flexi_field_name",

        # what value to store in this field
        "_value",

        # the tag
        "_tag",

        # the number of keys to store within this field
        "_instance_n_keys",

        # how deep in recursive fields this field resides.
        "_nested_level"
    ]

    def __init__(
            self, flexi_field_name, value=None, instance_n_keys=None, tag=None,
            nested_level=0):
        # pylint: disable=too-many-arguments
        self._flexi_field_name = flexi_field_name
        self._value = value
        self._tag = tag
        self._instance_n_keys = instance_n_keys
        self._nested_level = nested_level

    @property
    def name(self):
        """ The name for this Flexible field
        """
        return self._flexi_field_name

    @property
    def value(self):
        return self._value

    @property
    def tag(self):
        return self._tag

    @property
    def instance_n_keys(self):
        return self._instance_n_keys

    def __eq__(self, other):
        if not isinstance(other, FlexiField):
            return False
        return (self._flexi_field_name == other.name and
                self._instance_n_keys == other.instance_n_keys and
                self._tag == other.tag)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        if self._instance_n_keys is not None:
            return (self._flexi_field_name, self._instance_n_keys,
                    self._tag).__hash__()
        return (self._flexi_field_name, self._value,
                self._tag).__hash__()

    def __repr__(self):
        return "ID:{}:IV:{}:INK:{}:TAG:{}".format(
            self._flexi_field_name, self._value, self._instance_n_keys,
            self._tag)
