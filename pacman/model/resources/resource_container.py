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
        :param iptags: the iptags required
        :param reverse_iptags: the reverse iptags required
        :param sdram_tags: the sdram tags required
        :type dtcm: None or \
                    :py:class:`pacman.models.resources.dtcm_resource.DTCMResource`
        :type sdram:None or \
                    :py:class:`pacman.models.resources.sdram_resource.SDRAMResource`
        :type cpu_cycles: None or \
                    :py:class:`pacman.models.resources.cpu_cycles_per_tick_resource.CPUCyclesPerTickResource`
        :type iptags: None or list of \
                    :py:class:`pacman.models.resources.iptag_resource.IPtagResource`
        :type reverse_iptags: None or list of \
                    :py:class:`pacman.models.resources.reverse_iptag_resource.ReverseIPtagResource`
        :type sdram_tags: None or \
                    :py:class:`pacman.models.resources.sdram_tag_resource.SDRAMtagResource`
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
            self._sdram_tags = SDRAMTagResource(0, None)
        if self._reverse_iptags is None:
            self._reverse_iptags = []
        if self._iptags is None:
            self._iptags = []

    @property
    def dtcm(self):
        return self._dtcm_usage

    def add_to_dtcm_usage(self, extra_usage):
        self._dtcm_usage.add_to_usage_value(extra_usage)

    @property
    def cpu_cycles(self):
        return self._cpu_cycles

    def add_to_cpu_usage(self, extra_usage):
        self._cpu_cycles.add_to_usage_value(extra_usage)

    @property
    def sdram(self):
        return self._sdram_usage

    def add_to_sdram_usage(self, extra_usage):
        self._sdram_usage.add_to_usage_value(extra_usage)

    @property
    def iptags(self):
        return self._iptags

    def add_to_iptag_usage(self, extra_tag):
        self._iptags.append(extra_tag)

    @property
    def reverse_iptags(self):
        return self._reverse_iptags

    def add_to_reverse_iptags(self, extra_tag):
        self._reverse_iptags.append(extra_tag)

    @property
    def tags(self):
        data = list()
        data.extend(self.iptags)
        data.extend(self.reverse_iptags)
        data.append(self.sdram_tags)
        return data

    @property
    def sdram_tags(self):
        return self._sdram_tags

    def add_to_sdram_tags(self, n_tags=None, tag_ids=None):
        self._sdram_tags.add_tags(n_tags, tag_ids)

    def extend(self, other_resource_container):

        # added cpu stuff
        self._cpu_cycles.add_to_usage_value(
            other_resource_container.cpu_cycles.get_value())

        # added dtcm
        self._dtcm_usage.add_to_usage_value(
            other_resource_container.dtcm.get_value())

        # add sdram usage
        self._sdram_usage.add_to_usage_value(
            other_resource_container.sdram.get_value())

        # add iptags
        self._iptags.extend(other_resource_container.iptags)

        # add reverse iptags
        self._reverse_iptags.extend(other_resource_container.reverse_iptags)

        # add sdram tags
        total = other_resource_container.sdram_tags.n_tags
        tad_ids = other_resource_container.sdram_tags.tag_ids

        if total is not None:
            self._sdram_tags.add_to_n_tags(total)
        if tad_ids is not None:
            self._sdram_tags.add_to_tag_ids(tad_ids)
