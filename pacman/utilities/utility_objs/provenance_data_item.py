

class ProvenanceDataItem(object):
    """
    container for provenance data
    """

    def __init__(self, name, item, needs_reporting_to_end_user=False,
                 message_to_end_user=None):
        self._name = name
        self._item = item
        self._needs_reporting_to_end_user = needs_reporting_to_end_user
        self._message_to_end_user = message_to_end_user

    @property
    def message_to_end_user(self):
        """
        property method for the message the end user should read when needed
        :return: the message or None if not needing reporting
        """
        return self._message_to_end_user

    @property
    def needs_reporting_to_end_user(self):
        """
        property method for stating if this provenance data entry needs
        reporting to the end user
        :return:
        """
        return self._needs_reporting_to_end_user

    @property
    def name(self):
        """
        property method for the name of this bit of provenance data
        :return: the name of this bit of provenance data
        """
        return self._name

    @property
    def item(self):
        """
        property method for the bit of provenance data
        :return: the bit of provenance data
        """
        return self._item

    def __repr__(self):
        """
        string representation of the provenance data item
        :return: string
        """
        return "{}:{}:{}:{}".format(
            self._name, self._item, self._needs_reporting_to_end_user,
        self._message_to_end_user)
