

class FlexiField(object):
    """
    FlexiField
    """

    def __init__(self, flexi_field_id, instance_value=None,
                 instance_n_keys=None):
        self._flexi_field_id = flexi_field_id
        self._instance_value = instance_value
        if instance_n_keys is not None:
            self._instance_n_keys = instance_n_keys
        else:
            self._instance_n_keys = None

    @property
    def id(self):
        """
        property method for getting the flexi_field_id for this Flexi field
        :return:
        """
        return self._flexi_field_id

    @property
    def instance_value(self):
        """

        :return:
        """
        return self._instance_value

    @property
    def instance_n_keys(self):
        """

        :return:
        """
        return self._instance_n_keys

    def __eq__(self, other):
        if not isinstance(other, FlexiField):
            return False
        else:
            if (self._flexi_field_id == other.id
                    and self._instance_n_keys == other.instance_n_keys):
                return True
            else:
                return False

    def __hash__(self):
        if self._instance_n_keys is not None:
            return (self._flexi_field_id, self._instance_n_keys).__hash__()
        else:
            return (self._flexi_field_id, self._instance_value).__hash__()

    def __repr__(self):
        return "ID:{}IV:{}:INK{}".format(
            self._flexi_field_id, self._instance_value, self._instance_n_keys)
