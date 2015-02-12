class ReportState(object):

    def __init__(self, partitioner_report, placer_report, router_report,
                 router_dat_based_report, routing_info_report):
        self._partitioner_report = partitioner_report
        self._placer_report = placer_report
        self._router_report = router_report
        self._router_dat_based_report = router_dat_based_report
        self._routing_info_report = routing_info_report

    @property
    def partitioner_report(self):
        return self._partitioner_report

    @property
    def placer_report(self):
        return self._placer_report

    @property
    def router_report(self):
        return self._router_report

    @property
    def router_dat_based_report(self):
        return self._router_dat_based_report

    @property
    def routing_info_report(self):
        return self._routing_info_report
