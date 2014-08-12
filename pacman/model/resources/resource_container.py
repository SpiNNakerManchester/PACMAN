

class ResourceContainer(object):

    def __init__(self, dtcm, sdram, cpu):
        """container object for the 3 types of resources so that ordering is no
        longer a risk

        :param dtcm: the amount of dtcm used
        :param sdram: the amount of sdram used
        :param cpu: the amount of cpu used
        :type dtcm: pacman.models.resources.dtcm_resource.dtcmResource
        :type sdram: pacman.models.resources.sdram_resource.sdramResource
        :type cpu: pacman.models.resources.cpu_resource.cpuResource
        :return a new pacman.models.resources.resource_container.ResourceContainer
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