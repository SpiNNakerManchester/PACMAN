

class ResourceContainer(object):
    """
    container for the resources used by a model
    """

    def __init__(self, dtcm, sdram, cpu):
        """container object for the 3 types of resources so that ordering is no
        longer a risk

        :param dtcm: the amount of dtcm used
        :param sdram: the amount of sdram used
        :param cpu: the amount of cpu used
        :type dtcm:\
                    :py:class:`pacman.models.resources.dtcm_resource.DTCMResource`
        :type sdram:\
                    :py:class:`pacman.models.resources.sdram_resource.SDRAMResource`
        :type cpu:\
                    :py:class:`pacman.models.resources.cpu_cycles_per_tick_resource.CPUCyclesPerTickResource`
        :rtype: pacman.models.resources.resource_container.ResourceContainer
        :raise None: does not raise any known exception

        """
        self._dtcm_usage = dtcm
        self._sdram_usage = sdram
        self._cpu = cpu

    @property
    def dtcm(self):
        return self._dtcm_usage

    @property
    def cpu(self):
        return self._cpu

    @property
    def sdram(self):
        return self._sdram_usage
