from abc import abstractproperty

from .abstract_virtual_vertex import AbstractVirtualVertex


# interface
class AbstractFPGAVertex(AbstractVirtualVertex):
    """ A vertex connected to an FPGA
    """

    __slots__ = ()

    @abstractproperty
    def fpga_link_id(self):
        """ The link of the FPGA to which the vertex is connected

        :rtype: int
        """

    @abstractproperty
    def fpga_id(self):
        """ The ID of the FPGA to which the vertex is connected

        :rtype: int
        """
