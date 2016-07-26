from pacman.model.resources.cpu_cycles_per_tick_resource import \
    CPUCyclesPerTickResource
from pacman.model.resources.dtcm_resource import DTCMResource
from pacman.model.resources.sdram_resource import SDRAMResource
from pacman.model.resources.sdram_tag_resource import SDRAMTagResource


class ResourceContainer(object):

    def __init__(
            self, dtcm=None, sdram=None, cpu_cycles=None, iptags=None,
            reverse_iptags=None, sdram_tags=None):
        """container object for the 3 types of resources so that ordering is no
        longer a risk

        :param dtcm: the amount of dtcm used
        :param sdram: the amount of sdram used
        :param cpu_cycles: the amount of cpu used
        :param iptags: the iptag required
        :param reverse_iptags:
        :param sdram_tags:
        :type dtcm: None or \
                    :py:class:`pacman.models.resources.dtcm_resource.DTCMResource`
        :type sdram:None or \
                    :py:class:`pacman.models.resources.sdram_resource.SDRAMResource`
        :type cpu_cycles: None or \
                    :py:class:`pacman.models.resources.cpu_cycles_per_tick_resource.CPUCyclesPerTickResource`
        :type
        :type
        :type
        :rtype: pacman.models.resources.resource_container.ResourceContainer
        :raise None: does not raise any known exception

        """
        self._dtcm_usage = dtcm
        self._sdram_usage = sdram
        self._cpu_cycles = cpu_cycles
        self._iptags = iptags
        self._reverse_iptags = reverse_iptags
        self._sdram_tags = sdram_tags

        # check for none resources
        if self._dtcm_usage is None:
            self._dtcm_usage = DTCMResource(0)
        if self._sdram_usage is None:
            self._sdram_usage = SDRAMResource(0)
        if self._cpu_cycles is None:
            self._cpu_cycles = CPUCyclesPerTickResource(0)
        if self._sdram_tags is None:
            self._sdram_tags = SDRAMTagResource(0)
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
