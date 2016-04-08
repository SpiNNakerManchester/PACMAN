

class ResourceContainer(object):
    """
    container for the resources used by a model
    """

    def __init__(self, dtcm, sdram, cpu, multicast_no_payload_packets_per_tic,
                 multicast_payload_packets_per_tic,
                 fixed_route_packets_per_tic):
        """container object for the 3 types of resources so that ordering is no
        longer a risk

        :param dtcm: the amount of dtcm used
        :param sdram: the amount of sdram used
        :param cpu: the amount of cpu used
        :param multicast_payload_packets_per_tic:
        the number of multicast packets with payloads transmitted per tick
        :param multicast_no_payload_packets_per_tic:
        the number of multicast packets without payloads transmitted per tick
        :param fixed_route_packets_per_tic:
        the number of packets transmitted per tick
        :type dtcm:\
                    :py:class:`pacman.models.resources.dtcm_resource.DTCMResource`
        :type sdram:\
                    :py:class:`pacman.models.resources.sdram_resource.SDRAMResource`
        :type cpu:\
                    :py:class:`pacman.models.resources.cpu_cycles_per_tick_resource.CPUCyclesPerTickResource`
        :type multicast_payload_packets_per_tic: \
            :py:class:`pacman.models.resources.multi_cast_payload_packets_per_tic.MultiCastPayloadPacketsPerTic`
        :type multicast_no_payload_packets_per_tic: \
            :py:class:`pacman.models.resources.multi_cast_no_payload_packets_per_tic.MultiCastNoPayloadPacketsPerTic`
        :type fixed_route_packets_per_tic: \
            :py:class:`pacman.models.resources.fixed_route_packets_per_tic.FixedRoutePacketsPerTic`
        :rtype: pacman.models.resources.resource_container.ResourceContainer
        :raise None: does not raise any known exception

        """
        self._dtcm_usage = dtcm
        self._sdram_usage = sdram
        self._cpu = cpu
        self._multicast_payload_packets_per_tic = \
            multicast_payload_packets_per_tic
        self._multicast_no_payload_packets_per_tic = \
            multicast_no_payload_packets_per_tic
        self._fixed_route_packets_per_tic = fixed_route_packets_per_tic

    @property
    def dtcm(self):
        return self._dtcm_usage

    @property
    def cpu(self):
        return self._cpu

    @property
    def sdram(self):
        return self._sdram_usage

    @property
    def multicast_payload_packets_per_tic(self):
        return self._multicast_payload_packets_per_tic

    @property
    def multicast_no_payload_packets_per_tic(self):
        return self._multicast_no_payload_packets_per_tic

    @property
    def fixed_route_packets_per_tic(self):
        return self._fixed_route_packets_per_tic
