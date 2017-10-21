from .abstract_virtual_vertex import AbstractVirtualVertex
from abc import abstractproperty


# interface
class AbstractSpiNNakerLinkVertex(AbstractVirtualVertex):
    """ A vertex connected to a SpiNNaker Link
    """

    __slots__ = ()

    @abstractproperty
    def spinnaker_link_id(self):
        """ The SpiNNaker Link that the vertex is connected to
        """
        return self._spinnaker_link_id
