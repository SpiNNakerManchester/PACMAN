from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractProvidesProvenanceData(object):
    """ Indicates that an object provides provenance data
    """

    def __init__(self):
        pass

    @abstractmethod
    def get_provenance_data_items(
            self, transceiver, placement=None):
        """ returns a iterable of provenance data items
        :param transceiver: the SpinnMan interface object
        :param placement: the placement object for this subvertex or None if\
                    the system does not require a placement object
        :return: iterable of provenance_data_item
        """
