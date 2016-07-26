from abc import abstractproperty

from pacman.model.graphs.abstract_base_vertex \
    import AbstractBaseVertex


class AbstractVirtualVertex(AbstractBaseVertex):
    """ A vertex which exists outside of the machine
    """

    __slots__ = ()

    @abstractproperty
    def spinnaker_link_id(self):
        """ The id of the SpiNNaker link to which the device is connected
        """
