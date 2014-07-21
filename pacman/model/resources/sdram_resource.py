from pacman.model.resources.abstract_resource import AbstractResource


class SDRAMResource(AbstractResource):
    """ Represents an amount of SDRAM used or available on a chip in the machine
    """
    
    def __init__(self, sdram):
        """
        
        :param sdram: The amount of SDRAM in bytes
        :type sdram: int
        :raise None: No known exceptions are raised
        """
        self._sdram = sdram
    
    def get_value(self):
        """ See :py:meth:`pacman.model.resources.abstract_resource.AbstractResource.get_value`
        """
        return self._sdram
