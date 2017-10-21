from .abstract_resource import AbstractResource


class CoreResource(AbstractResource):
    """ Represents the number of cores that need to be allocated
    """

    __slots__ = [

        # The number of cores that need to be allocated on a give chip
        "_n_cores",

        # the chip that has these cores allocated
        "_chip"
    ]

    def __init__(self, chip, n_cores):
        """

        :param n_cores: The number of cores to allocate
        :type n_cores: int
        :param chip: chip of where these cores are to be allocated
        :type chip: SpiNNMachine.chip.Chip
        :raise None: No known exceptions are raised
        """
        self._n_cores = n_cores
        self._chip = chip

    @property
    def n_cores(self):
        return self._n_cores

    @property
    def chip(self):
        return self._chip

    def get_value(self):
        return self._chip, self._n_cores
