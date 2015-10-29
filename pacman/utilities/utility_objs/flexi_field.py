

class FlexiField(object):
    """
    FlexiField
    """

    def __init__(self, flexi_field_id, instance_value=None,
                 instance_range=None):
        self._flexi_field_id = flexi_field_id
        self._instance_value = instance_value
        if instance_range is not None:
            self._instance_range_hi = instance_range.hi_atom
            self._instance_range_lo = instance_range.lo_atom
        else:
            self._instance_range_hi = None
            self._instance_range_lo = None

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
    def instance_range_hi(self):
        """

        :return:
        """
        return self._instance_range_hi

    @property
    def instance_range_lo(self):
        """

        :return:
        """
        return self._instance_range_lo

    @property
    def instance_range(self):
        """

        :return:
        """
        return (self.instance_range_hi, self._instance_range_lo)

    def __eq__(self, other):
        if not isinstance(other, FlexiField):
            return False
        else:
            if self._flexi_field_id == other.id:
                return True
            else:
                return False

    def __hash__(self):
        if self._instance_range_hi is not None:
            return (self._flexi_field_id, self._instance_range_hi,
                    self._instance_range_lo).__hash__()
        else:
            return (self._flexi_field_id, self._instance_value).__hash__()

    def __repr__(self):
        return "{}:{}:{}:{}".format(
            self._flexi_field_id, self._instance_value, self._instance_range_lo,
            self._instance_range_hi)
