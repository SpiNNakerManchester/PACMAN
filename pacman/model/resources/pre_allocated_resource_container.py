class PreAllocatedResourceContainer(object):
    """ container object for pre-allocated resources

    """

    __slots__ = [


        # a iterable of SpecificSDRAMResource object that reflects the amount
        # of SDRAM (in bytes) pre allocated on a specific chip on the SpiNNaker
        #  machine
        "_specific_sdram_usage",

        # A iterable of SpecificCoreResource objects that reflect the number
        # of specific cores that have been pre allocated on a chip.
        "_specific_core_resources",

        # A iterable of CoreResource objects that reflect the number of
        #  cores that have been pre allocated on a chip, but which don't care
        # which core it uses.
        "_core_resources"
    ]

    def __init__(
            self, specific_sdram_usage=None, specific_core_resources=None,
            core_resources=None):
        """ Container object for the types of resources

        :param specific_sdram_usage:\
            iterable of SpecificSDRAMResource which states that specific chips\
            have missing SDRAM
        :type specific_sdram_usage: iterable of \
            pacman.model.resources.SpecificSDRAMResource
        :param  specific_core_resources:\
            states which cores have been preallocated
        :type specific_core_resources: iterable of \
            pacman.model.resources.SpecificCoreResource
        :param core_resources:\
            states a number of cores have been pre allocated but don't care
            which ones they are
        :type core_resources: pacman.model.resources.CoreResource

        """
        self._specific_sdram_usage = specific_sdram_usage
        self._specific_core_resources = specific_core_resources
        self._core_resources = core_resources

        # check for none resources
        if self._specific_sdram_usage is None:
            self._specific_sdram_usage = []
        if self._specific_core_resources is None:
            self._specific_core_resources = []
        if self._core_resources is None:
            self._core_resources = []

    @property
    def specific_sdram_usage(self):
        return self._specific_sdram_usage

    @property
    def specific_core_resources(self):
        return self._specific_core_resources

    @property
    def core_resources(self):
        return self._core_resources

    def extend(self, other):

        # add specific sdram usage
        self._specific_sdram_usage.extend(other.specific_sdram_usage)

        # add specific cores
        self._specific_core_resources.extend(other.specific_core_resources)

        # add none specific cores
        self._core_resources.extend(other.core_resources)
