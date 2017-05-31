from pacman.model.resources.cpu_cycles_per_tick_resource import \
    CPUCyclesPerTickResource
from pacman.model.resources.dtcm_resource import DTCMResource
from pacman.model.resources.sdram_resource import SDRAMResource


class PreAllocatedResourceContainer(object):
    """container object for the types of resources so that ordering is no
        longer a risk

    """

    __slots__ = [


        # a iterable of SpecificSDRAMResource object that reflects the amount
        # of SDRAM (in bytes) pre allocated on a specific chip on the SpiNNaker
        #  machine
        "_specific_sdram_usage",

        # A iterable of SpecificCoreResource objects that reflect the number
        # of specific cores that have been pre allocated on a chip.
        "_specific_cores_resource",

        # A iterable of CoreResource objects that reflect the number of
        #  cores that have been pre allocated on a chip, but which dont care
        # which core it uses.
        "_core_resources"
    ]

    def __init__(
            self, specific_sdram_usage=None, specific_cores_resource=None,
            core_resources=None):
        """ Container object for the types of resources

        :param _specific_sdram_usage: iterable of SpecificSDRAMResource
         which states that specific chips have missing sdram
        :type _specific_sdram_usage: iterable of SpecificSDRAMResource
        :param  specific_cores_resource: states which cores have been pre
         allocated
        :type specific_cores_resource: iterable of SpecificCoreResource
        :param core_resources states a number of coers have been pre allocated
         but dont care which ones they are
        :type core_resources: CoreResource
        :rtype: pacman.models.resources.pre_allocated_resource_container.PreAllocatedResourceContainer
        :raise None: does not raise any known exception

        """
        self._specific_sdram_usage = specific_sdram_usage
        self._specific_cores_resource = specific_cores_resource
        self._core_resources = core_resources

        # check for none resources
        if self._specific_sdram_usage is None:
            self._specific_sdram_usage = []
        if self._specific_cores_resource is None:
            self._specific_cores_resource = []
        if self._core_resources is None:
            self._core_resources = []

    @property
    def specific_sdram_usage(self):
        return self._specific_sdram_usage

    @property
    def specific_cores_resource(self):
        return self._specific_cores_resource

    @property
    def core_resources(self):
        return self._core_resources

    def extend(self, other):

        # add specific sdram usage
        self._specific_sdram_usage.extend(other.specific_sdram_usage)

        # add specific cores
        self._specific_cores_resource.extend(other.specific_cores_resource)

        # add none specific cores
        self._core_resources.extend(other.core_resources)
