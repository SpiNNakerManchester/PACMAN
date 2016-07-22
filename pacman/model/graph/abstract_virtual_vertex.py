from pacman.model.graph.abstract_vertex import AbstractVertex
from abc import abstractproperty


class AbstractVirtualVertex(AbstractVertex):
    """ A vertex which exists outside of the machine
    """

    __slots__ = ()

    @abstractproperty
    def spinnaker_link_id(self):
        """ The id of the SpiNNaker link to which the device is connected
        """
