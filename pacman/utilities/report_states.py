"""
ReportState
"""


class ReportState(object):
    """
    helper class to store report states
    """

    def __init__(self, partitioner_report,
                 placer_report_with_partitionable_graph,
                 placer_report_without_partitionable_graph,
                 router_report, routing_info_report, tag_allocation_report):
        self._partitioner_report = partitioner_report
        self._placer_report_with_partitionable_graph = \
            placer_report_with_partitionable_graph
        self._placer_report_without_partitionable_graph = \
            placer_report_without_partitionable_graph
        self._router_report = router_report
        self._routing_info_report = routing_info_report
        self._tag_allocation_report = tag_allocation_report

    @property
    def partitioner_report(self):
        """
        returns if the partitioner report should be ran
        :return:
        """
        return self._partitioner_report

    @property
    def placer_report_with_partitionable_graph(self):
        """
        retruns if the placer with partitionable graph should be ran
        :return:
        """
        return self._placer_report_with_partitionable_graph

    @property
    def placer_report_without_partitionable_graph(self):
        """
        retruns if the placer without partitionable graph should be ran
        :return:
        """
        return self._placer_report_without_partitionable_graph

    @property
    def router_report(self):
        """
        retursn if the router report should be ran
        :return:
        """
        return self._router_report

    @property
    def routing_info_report(self):
        """
        returns if the router info report should be ran
        :return:
        """
        return self._routing_info_report

    @property
    def tag_allocation_report(self):
        """
        returns if the tag allocator should be ran
        :return:
        """
        return self._tag_allocation_report
