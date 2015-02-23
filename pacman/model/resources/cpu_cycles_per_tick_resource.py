from pacman.model.abstract_classes.abstract_resource import AbstractResource


class CPUCyclesPerTickResource(AbstractResource):
    """ Represents the number of CPU clock cycles per tick used or available\
        on a core of a chip in the machine
    """
    
    def __init__(self, cycles):
        """
        
        :param cycles: The number of CPU clock cycles
        :type cycles: int
        :raise None: No known exceptions are raised
        """
        self._cycles = cycles
    
    def get_value(self):
        """ See :py:meth:`pacman.model.resources.abstract_resource\
        .AbstractResource.get_value`
        """
        return self._cycles
