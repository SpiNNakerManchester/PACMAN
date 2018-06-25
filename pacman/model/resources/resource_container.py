from .cpu_cycles_per_tick_resource import CPUCyclesPerTickResource
from .dtcm_resource import DTCMResource
from .sdram_resource import SDRAMResource


class ResourceContainer(object):
    """ Container for the types of resources so that ordering is no\
        longer a problem.
    """

    __slots__ = [

        # a DTCMResource object that reflects the amount of DTCM (in bytes)
        # used by a machine vertex on the SpiNNaker machine
        "_dtcm_usage",

        # a SDRAMResource object that reflects the amount of SDRAM (in bytes)
        # used by a machine vertex on the SpiNNaker machine
        "_sdram_usage",

        # a CPUCyclesPerTickResource object that reflects the number of
        # CPU cycles the machine vertex is expected to use on a SpiNNaker
        # machine
        "_cpu_cycles",

        # An iterable of IPtagResource objects that reflect the number of IP
        # tags a machine vertex is going to use on a SpiNNaker machine, as well
        # as the configuration data of said IP tags.
        "_iptags",

        # A iterable of ReverseIPtagResource objects that reflect the number of
        # Reverse IP tags a machine vertex is going to use on a SpiNNaker
        # machine, as well as the configuration data of said reverse IP tags.
        "_reverse_iptags"
    ]

    def __init__(
            self, dtcm=None, sdram=None, cpu_cycles=None, iptags=None,
            reverse_iptags=None):
        """ Container object for the types of resources

        :param dtcm: the amount of dtcm used
        :param sdram: the amount of SDRAM used
        :param cpu_cycles: the amount of CPU used
        :param iptags: the IP tags required
        :param reverse_iptags: the reverse IP tags required
        :type dtcm: None or \
            :py:class:`pacman.models.resources.dtcm_resource.DTCMResource`
        :type sdram: None or \
            :py:class:`pacman.models.resources.sdram_resource.SDRAMResource`
        :type cpu_cycles: None or \
            :py:class:`pacman.models.resources.cpu_cycles_per_tick_resource.CPUCyclesPerTickResource`
        :type iptags: None or \
            list(:py:class:`pacman.models.resources.iptag_resource.IPtagResource`)
        :type reverse_iptags: None or \
            list(:py:class:`pacman.models.resources.reverse_iptag_resource.ReverseIPtagResource`)
        :rtype: pacman.models.resources.resource_container.ResourceContainer
        :raise None: does not raise any known exception
        """
        # pylint: disable=too-many-arguments
        self._dtcm_usage = dtcm
        self._sdram_usage = sdram
        self._cpu_cycles = cpu_cycles
        self._iptags = iptags
        self._reverse_iptags = reverse_iptags

        # check for none resources
        if self._dtcm_usage is None:
            self._dtcm_usage = DTCMResource(0)
        if self._sdram_usage is None:
            self._sdram_usage = SDRAMResource(0)
        if self._cpu_cycles is None:
            self._cpu_cycles = CPUCyclesPerTickResource(0)
        if self._reverse_iptags is None:
            self._reverse_iptags = []
        if self._iptags is None:
            self._iptags = []

    @property
    def dtcm(self):
        return self._dtcm_usage

    @property
    def cpu_cycles(self):
        return self._cpu_cycles

    @property
    def sdram(self):
        return self._sdram_usage

    @property
    def iptags(self):
        return self._iptags

    @property
    def reverse_iptags(self):
        return self._reverse_iptags

    @property
    def sdram_tags(self):
        return self._sdram_tags

    def extend(self, other):

        # added CPU stuff
        self._cpu_cycles = CPUCyclesPerTickResource(
            self._cpu_cycles.get_value() + other.cpu_cycles.get_value())

        # added dtcm
        self._dtcm_usage = DTCMResource(
            self._dtcm_usage.get_value() + other.dtcm.get_value())

        # add SDRAM usage
        self._sdram_usage = SDRAMResource(
            self._sdram_usage.get_value() + other.sdram.get_value())

        # add IPtags
        self._iptags.extend(other.iptags)

        # add reverse IPtags
        self._reverse_iptags.extend(other.reverse_iptags)
