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
    def write_provenance_data_in_xml(self, file_path, transceiver,
                                     placement=None):
        """ Write the provenance data using XML
        :param file_path: the file path to write the provenance data to
        :param transceiver: the spinnman interface object
        :param placement: the placement object for this subvertex or None if\
                    the system does not require a placement object
        :return: None
        """
